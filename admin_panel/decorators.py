from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.core.exceptions import PermissionDenied
import logging

from .models import AdminUser, SessionSecurity, AuditLog

logger = logging.getLogger(__name__)

def admin_required(view_func):
    """Decorator to ensure user is an admin"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin_panel:login')
        
        try:
            admin_user = AdminUser.objects.get(user=request.user)
            if not admin_user.is_active_admin:
                messages.error(request, "Your admin account is not active.")
                return redirect('admin_panel:login')
            
            # Check session security
            if not is_session_secure(request, admin_user):
                messages.error(request, "Session security violation detected.")
                return redirect('admin_panel:login')
            
            # Add admin_user to request for easy access
            request.admin_user = admin_user
            
        except AdminUser.DoesNotExist:
            messages.error(request, "Access denied. Admin privileges required.")
            return redirect('admin_panel:login')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def role_required(*required_roles):
    """Decorator to check specific admin roles"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request, 'admin_user'):
                return redirect('admin_panel:login')
            
            admin_user = request.admin_user
            
            # Handle both single roles and lists of roles
            if required_roles and isinstance(required_roles[0], list):
                roles_to_check = required_roles[0]
            else:
                roles_to_check = required_roles
            
            # Super admin has access to all roles
            if admin_user.role and admin_user.role.name == 'superadmin':
                return view_func(request, *args, **kwargs)
            
            if not admin_user.role or admin_user.role.name not in roles_to_check:
                if request.headers.get('Accept') == 'application/json':
                    return JsonResponse({
                        'error': 'Insufficient permissions',
                        'message': f'Required roles: {", ".join(roles_to_check)}'
                    }, status=403)
                
                messages.error(request, f"Access denied. Required roles: {', '.join(roles_to_check)}")
                return redirect('admin_panel:dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def permission_required(*permissions):
    """Decorator to check specific permissions"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request, 'admin_user'):
                return redirect('admin_panel:login')
            
            admin_user = request.admin_user
            
            # Super admin has all permissions
            if admin_user.role and admin_user.role.name == 'superadmin':
                return view_func(request, *args, **kwargs)
            
            # Check if user has required permissions
            user_permissions = admin_user.user.get_all_permissions()
            role_permissions = set()
            if admin_user.role:
                role_permissions = set(admin_user.role.permissions.values_list('codename', flat=True))
            
            all_permissions = user_permissions.union(role_permissions)
            
            for permission in permissions:
                if permission not in all_permissions:
                    if request.headers.get('Accept') == 'application/json':
                        return JsonResponse({
                            'error': 'Insufficient permissions',
                            'message': f'Required permission: {permission}'
                        }, status=403)
                    
                    messages.error(request, f"Access denied. Required permission: {permission}")
                    return redirect('admin_panel:dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def is_session_secure(request, admin_user):
    """Check if session is secure"""
    try:
        session_security = SessionSecurity.objects.get(
            user=admin_user.user,
            session_key=request.session.session_key
        )
        
        # Check if session is expired
        if session_security.is_expired:
            session_security.delete()
            return False
        
        # Check IP address (optional - can be disabled for mobile users)
        current_ip = get_client_ip(request)
        if session_security.ip_address != current_ip:
            logger.warning(f"IP address mismatch for user {admin_user.user.username}: "
                          f"session IP {session_security.ip_address} vs current IP {current_ip}")
            # Uncomment the next line to enforce IP checking
            # return False
        
        # Update last activity
        session_security.last_activity = timezone.now()
        session_security.save()
        
        return True
    
    except SessionSecurity.DoesNotExist:
        return False

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_admin_action(user, action, description, object_instance=None, old_values=None, new_values=None, ip_address=None, user_agent=None):
    """Log admin actions for audit trail"""
    try:
        from django.contrib.contenttypes.models import ContentType
        
        content_type = None
        object_id = None
        object_repr = ''
        
        if object_instance:
            content_type = ContentType.objects.get_for_model(object_instance)
            object_id = object_instance.pk
            object_repr = str(object_instance)
        
        AuditLog.objects.create(
            user=user,
            action=action,
            content_type=content_type,
            object_id=object_id,
            object_repr=object_repr,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            old_values=old_values,
            new_values=new_values
        )
        
    except Exception as e:
        logger.error(f"Failed to log admin action: {e}")

def create_password_reset_token(user):
    """Create a password reset token"""
    from .models import PasswordResetToken
    
    # Invalidate existing tokens
    PasswordResetToken.objects.filter(user=user, used=False).update(used=True)
    
    # Create new token
    token = PasswordResetToken.objects.create(
        user=user,
        expires_at=timezone.now() + timezone.timedelta(hours=24)
    )
    
    return token

def get_admin_menu_items(admin_user):
    """Get menu items based on admin role"""
    menu_items = []
    
    if not admin_user.role:
        return menu_items
    
    role = admin_user.role.name
    
    # Dashboard - available to all
    menu_items.append({
        'name': 'Dashboard',
        'url': 'admin_panel:dashboard',
        'icon': 'dashboard'
    })
    
    # Super Admin and Admin
    if role in ['superadmin', 'admin']:
        menu_items.extend([
            {
                'name': 'User Management',
                'url': 'admin_panel:user_list',
                'icon': 'users'
            },
            {
                'name': 'Roles & Permissions',
                'url': 'admin_panel:role_list',
                'icon': 'shield'
            },
            {
                'name': 'Audit Logs',
                'url': 'admin_panel:audit_logs',
                'icon': 'file-text'
            }
        ])
    
    # Merchandiser and Admin
    if role in ['superadmin', 'admin', 'merchandiser']:
        menu_items.extend([
            {
                'name': 'Products',
                'url': 'admin_panel:product_list',
                'icon': 'package'
            },
            {
                'name': 'Categories',
                'url': 'admin_panel:category_list',
                'icon': 'folder'
            },
            {
                'name': 'Price Management',
                'url': 'admin_panel:price_history',
                'icon': 'dollar-sign'
            }
        ])
    
    # Inventory Manager and Admin
    if role in ['superadmin', 'admin', 'inventory']:
        menu_items.extend([
            {
                'name': 'Inventory',
                'url': 'admin_panel:inventory_overview',
                'icon': 'box'
            },
            {
                'name': 'Stock Adjustments',
                'url': 'admin_panel:stock_adjustments',
                'icon': 'edit'
            },
            {
                'name': 'Low Stock Alerts',
                'url': 'admin_panel:low_stock_alerts',
                'icon': 'alert-triangle'
            }
        ])
    
    # CRM Manager and Admin
    if role in ['superadmin', 'admin', 'crm']:
        menu_items.extend([
            {
                'name': 'Customers',
                'url': 'admin_panel:customer_list',
                'icon': 'users'
            },
            {
                'name': 'Orders',
                'url': 'admin_panel:order_list',
                'icon': 'shopping-cart'
            },
            {
                'name': 'AI Predictions',
                'url': 'admin_panel:ai_predictions',
                'icon': 'brain'
            }
        ])
    
    # Data Analyst and Admin
    if role in ['superadmin', 'admin', 'analyst']:
        menu_items.extend([
            {
                'name': 'Analytics',
                'url': 'admin_panel:analytics_dashboard',
                'icon': 'bar-chart'
            },
            {
                'name': 'Reports',
                'url': 'admin_panel:reports',
                'icon': 'file-text'
            },
            {
                'name': 'AI Impact',
                'url': 'admin_panel:ai_impact',
                'icon': 'trending-up'
            }
        ])
    
    return menu_items
