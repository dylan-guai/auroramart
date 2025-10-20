from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum, F
from django.core.paginator import Paginator
import logging
import json
import csv

from .models import AdminUser, AdminRole, AuditLog, LoginAttempt, PasswordResetToken, SessionSecurity
from .forms import AdminLoginForm, AdminPasswordResetForm, AdminPasswordChangeForm, AdminUserCreationForm, AdminUserUpdateForm
from .decorators import admin_required, role_required
from .utils import log_admin_action, get_client_ip, create_password_reset_token

logger = logging.getLogger(__name__)

def admin_login(request):
    """Enhanced admin login with security features"""
    if request.user.is_authenticated:
        return redirect('admin_panel:dashboard')
    
    if request.method == 'POST':
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)
            
            # Get client IP and user agent
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Check if user exists and is admin
            try:
                user = User.objects.get(username=username)
                admin_user = AdminUser.objects.get(user=user)
                
                # Check if account is locked
                if admin_user.is_locked:
                    LoginAttempt.objects.create(
                        username=username,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=False,
                        failure_reason="Account locked"
                    )
                    messages.error(request, "Account is temporarily locked. Please try again later.")
                    return render(request, 'admin_panel/login.html', {'form': form})
                
                # Authenticate user
                user = authenticate(request, username=username, password=password)
                
                if user and admin_user.is_active_admin:
                    # Successful login
                    login(request, user)
                    
                    # Update admin user info
                    admin_user.last_login_ip = ip_address
                    admin_user.failed_login_attempts = 0
                    admin_user.save()
                    
                    # Set session expiry based on remember me
                    if not remember_me:
                        request.session.set_expiry(0)  # Browser close
                    else:
                        request.session.set_expiry(30 * 24 * 60 * 60)  # 30 days
                    
                    # Log successful login
                    LoginAttempt.objects.create(
                        username=username,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=True
                    )
                    
                    # Create session security record
                    SessionSecurity.objects.create(
                        user=user,
                        session_key=request.session.session_key,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        expires_at=timezone.now() + timezone.timedelta(days=30 if remember_me else 1)
                    )
                    
                    # Log admin action
                    log_admin_action(
                        user=user,
                        action='login',
                        description=f'Admin login from {ip_address}',
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                    
                    messages.success(request, f"Welcome back, {user.get_full_name()}!")
                    return redirect('admin_panel:dashboard')
                else:
                    # Failed login
                    admin_user.failed_login_attempts += 1
                    
                    # Lock account after 5 failed attempts
                    if admin_user.failed_login_attempts >= 5:
                        admin_user.lock_account(minutes=30)
                        failure_reason = "Account locked after 5 failed attempts"
                    else:
                        failure_reason = f"Invalid credentials (attempt {admin_user.failed_login_attempts}/5)"
                    
                    admin_user.save()
                    
                    LoginAttempt.objects.create(
                        username=username,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=False,
                        failure_reason=failure_reason
                    )
                    
                    messages.error(request, "Invalid username or password.")
            except (User.DoesNotExist, AdminUser.DoesNotExist):
                LoginAttempt.objects.create(
                    username=username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    failure_reason="User not found or not admin"
                )
                messages.error(request, "Invalid username or password.")
    else:
        form = AdminLoginForm()
    
    return render(request, 'admin_panel/login.html', {'form': form})

@login_required
@admin_required
def admin_logout(request):
    """Enhanced admin logout with audit logging"""
    user = request.user
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Log admin action
    log_admin_action(
        user=user,
        action='logout',
        description=f'Admin logout from {ip_address}',
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    # Remove session security record
    SessionSecurity.objects.filter(
        user=user,
        session_key=request.session.session_key
    ).delete()
    
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('admin_panel:login')

def admin_password_reset_request(request):
    """Request password reset via email"""
    if request.method == 'POST':
        form = AdminPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            try:
                user = User.objects.get(email=email)
                admin_user = AdminUser.objects.get(user=user)
                
                if admin_user.is_active_admin:
                    # Create password reset token
                    token = create_password_reset_token(user)
                    
                    # Send email
                    reset_url = request.build_absolute_uri(
                        f'/admin/reset-password/{token.token}/'
                    )
                    
                    send_mail(
                        'AuroraMart Admin Password Reset',
                        f'''
                        You requested a password reset for your AuroraMart admin account.
                        
                        Click the link below to reset your password:
                        {reset_url}
                        
                        This link will expire in 24 hours.
                        
                        If you did not request this reset, please ignore this email.
                        ''',
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=False,
                    )
                    
                    messages.success(request, "Password reset link sent to your email.")
                    return redirect('admin_panel:login')
                else:
                    messages.error(request, "Account is not active.")
            except (User.DoesNotExist, AdminUser.DoesNotExist):
                messages.error(request, "No admin account found with this email.")
    else:
        form = AdminPasswordResetForm()
    
    return render(request, 'admin_panel/password_reset_request.html', {'form': form})

def admin_password_reset_confirm(request, token):
    """Confirm password reset with token"""
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
        
        if not reset_token.is_valid:
            messages.error(request, "Password reset link has expired or been used.")
            return redirect('admin_panel:login')
        
        if request.method == 'POST':
            form = AdminPasswordChangeForm(request.POST)
            if form.is_valid():
                password = form.cleaned_data['new_password1']
                
                # Update password
                user = reset_token.user
                user.set_password(password)
                user.save()
                
                # Mark token as used
                reset_token.used = True
                reset_token.used_at = timezone.now()
                reset_token.save()
                
                # Log admin action
                log_admin_action(
                    user=user,
                    action='password_change',
                    description='Password reset via email',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, "Password reset successfully. Please log in with your new password.")
                return redirect('admin_panel:login')
        else:
            form = AdminPasswordChangeForm()
        
        return render(request, 'admin_panel/password_reset_confirm.html', {
            'form': form,
            'token': token
        })
    
    except PasswordResetToken.DoesNotExist:
        messages.error(request, "Invalid password reset link.")
        return redirect('admin_panel:login')

@login_required
@admin_required
def admin_password_change(request):
    """Change password while logged in"""
    if request.method == 'POST':
        form = AdminPasswordChangeForm(request.POST)
        if form.is_valid():
            user = request.user
            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            
            # Log out all other sessions
            SessionSecurity.objects.filter(user=user).exclude(
                session_key=request.session.session_key
            ).delete()
            
            # Log admin action
            log_admin_action(
                user=user,
                action='password_change',
                description='Password changed via admin panel',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, "Password changed successfully. You have been logged out of other sessions.")
            return redirect('admin_panel:login')
    else:
        form = AdminPasswordChangeForm()
    
    return render(request, 'admin_panel/password_change.html', {'form': form})

@admin_required
def admin_dashboard(request):
    """Main admin dashboard"""
    # Get admin user
    admin_user = AdminUser.objects.get(user=request.user)
    
    # Get menu items for this role
    from .utils import get_admin_menu_items
    menu_items = get_admin_menu_items(admin_user)
    
    # Import customer-facing models
    from profiles.models import Profile
    from checkout.models import Order, OrderItem
    from item.models import Product
    
    # Get real dashboard data
    total_customers = Profile.objects.count()
    total_orders = Order.objects.count()
    total_products = Product.objects.count()
    
    # Calculate total revenue
    total_revenue = Order.objects.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Get low stock items
    low_stock_items = Product.objects.filter(
        stock_quantity__lte=F('reorder_threshold')
    ).count()
    
    # Get recent orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:5]
    
    # Get top products by sales
    top_products = Product.objects.annotate(
        total_sold=Sum('orderitem__quantity')
    ).order_by('-total_sold')[:5]
    
    # Get additional dashboard data
    from datetime import timedelta
    from checkout.models import OrderReturn
    
    # New customers this month
    this_month = timezone.now().replace(day=1)
    new_customers_this_month = Profile.objects.filter(
        user__date_joined__gte=this_month
    ).count()
    
    # Pending orders
    pending_orders = Order.objects.filter(status__in=['pending', 'confirmed']).count()
    
    # Revenue this month
    revenue_this_month = Order.objects.filter(
        created_at__gte=this_month,
        payment_status='paid'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Pending return requests
    pending_returns = OrderReturn.objects.filter(status='pending').select_related('order', 'order__user')[:5]
    
    # Dashboard data
    context = {
        'admin_user': admin_user,
        'menu_items': menu_items,
        'recent_logins': LoginAttempt.objects.filter(success=True).order_by('-timestamp')[:10],
        'failed_logins': LoginAttempt.objects.filter(success=False).order_by('-timestamp')[:10],
        'recent_audit_logs': AuditLog.objects.order_by('-timestamp')[:10],
        'total_customers': total_customers,
        'total_orders': total_orders,
        'total_products': total_products,
        'total_revenue': total_revenue,
        'low_stock_items': low_stock_items,
        'recent_orders': recent_orders,
        'top_products': top_products,
        'new_customers_this_month': new_customers_this_month,
        'pending_orders': pending_orders,
        'revenue_this_month': revenue_this_month,
        'pending_returns': pending_returns,
    }
    
    return render(request, 'admin_panel/dashboard.html', context)

# User Management Views
@login_required
@admin_required
@role_required('superadmin', 'admin')
def admin_user_list(request):
    """List all admin users with filtering and search"""
    admin_users = AdminUser.objects.select_related('user', 'role').all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        admin_users = admin_users.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(employee_id__icontains=search_query)
        )
    
    # Filter by role
    role_filter = request.GET.get('role', '')
    if role_filter:
        admin_users = admin_users.filter(role__name=role_filter)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        admin_users = admin_users.filter(is_active_admin=True)
    elif status_filter == 'inactive':
        admin_users = admin_users.filter(is_active_admin=False)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(admin_users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get menu items
    from .utils import get_admin_menu_items
    menu_items = get_admin_menu_items(request.admin_user)
    
    context = {
        'admin_user': request.admin_user,
        'menu_items': menu_items,
        'page_obj': page_obj,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'roles': AdminRole.objects.filter(is_active=True),
    }
    
    return render(request, 'admin_panel/user_list.html', context)

@login_required
@admin_required
@role_required('superadmin', 'admin')
def admin_user_create(request):
    """Create new admin user"""
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create AdminUser profile
            admin_user = AdminUser.objects.create(
                user=user,
                role=form.cleaned_data.get('role'),
                employee_id=form.cleaned_data.get('employee_id'),
                department=form.cleaned_data.get('department'),
                phone=form.cleaned_data.get('phone'),
                is_active_admin=True
            )
            
            # Log admin action
            log_admin_action(
                user=request.user,
                action='create',
                object_instance=admin_user,
                description=f'Created admin user: {user.username}',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'Admin user "{user.username}" created successfully.')
            return redirect('admin_panel:user_detail', user_id=user.id)
    else:
        form = AdminUserCreationForm()
    
    # Get menu items
    from .utils import get_admin_menu_items
    menu_items = get_admin_menu_items(request.admin_user)
    
    context = {
        'admin_user': request.admin_user,
        'menu_items': menu_items,
        'form': form,
    }
    
    return render(request, 'admin_panel/user_create.html', context)

@login_required
@admin_required
@role_required('superadmin', 'admin')
def admin_user_detail(request, user_id):
    """View admin user details"""
    try:
        user = User.objects.get(id=user_id)
        admin_user = AdminUser.objects.get(user=user)
    except (User.DoesNotExist, AdminUser.DoesNotExist):
        messages.error(request, 'Admin user not found.')
        return redirect('admin_panel:user_list')
    
    # Get recent audit logs for this user
    recent_logs = AuditLog.objects.filter(user=user).order_by('-timestamp')[:10]
    
    # Get login attempts
    recent_logins = LoginAttempt.objects.filter(username=user.username).order_by('-timestamp')[:10]
    
    # Get menu items
    from .utils import get_admin_menu_items
    menu_items = get_admin_menu_items(request.admin_user)
    
    context = {
        'admin_user': request.admin_user,
        'menu_items': menu_items,
        'user': user,
        'admin_user_profile': admin_user,
        'recent_logs': recent_logs,
        'recent_logins': recent_logins,
    }
    
    return render(request, 'admin_panel/user_detail.html', context)

@login_required
@admin_required
@role_required('superadmin', 'admin')
def admin_user_edit(request, user_id):
    """Edit admin user"""
    try:
        user = User.objects.get(id=user_id)
        admin_user = AdminUser.objects.get(user=user)
    except (User.DoesNotExist, AdminUser.DoesNotExist):
        messages.error(request, 'Admin user not found.')
        return redirect('admin_panel:user_list')
    
    if request.method == 'POST':
        form = AdminUserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            # Save user data
            user = form.save()
            
            # Update admin user profile
            admin_user.role = form.cleaned_data.get('role')
            admin_user.department = form.cleaned_data.get('department')
            admin_user.phone = form.cleaned_data.get('phone')
            admin_user.save()
            
            # Log admin action
            log_admin_action(
                user=request.user,
                action='update',
                object_instance=admin_user,
                description=f'Updated admin user: {user.username}',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'Admin user "{user.username}" updated successfully.')
            return redirect('admin_panel:user_detail', user_id=user.id)
    else:
        form = AdminUserUpdateForm(instance=user)
        form.fields['role'].initial = admin_user.role
        form.fields['department'].initial = admin_user.department
        form.fields['phone'].initial = admin_user.phone
    
    # Get menu items
    from .utils import get_admin_menu_items
    menu_items = get_admin_menu_items(request.admin_user)
    
    context = {
        'admin_user': request.admin_user,
        'menu_items': menu_items,
        'form': form,
        'user': user,
        'admin_user_profile': admin_user,
    }
    
    return render(request, 'admin_panel/user_edit.html', context)

@login_required
@admin_required
@role_required('superadmin', 'admin')
@require_POST
def admin_user_toggle(request, user_id):
    """Toggle admin user active status"""
    try:
        user = User.objects.get(id=user_id)
        admin_user = AdminUser.objects.get(user=user)
    except (User.DoesNotExist, AdminUser.DoesNotExist):
        return JsonResponse({'success': False, 'message': 'Admin user not found.'})
    
    # Prevent deactivating self
    if user == request.user:
        return JsonResponse({'success': False, 'message': 'Cannot deactivate your own account.'})
    
    # Toggle status
    admin_user.is_active_admin = not admin_user.is_active_admin
    admin_user.save()
    
    # Log admin action
    action = 'activated' if admin_user.is_active_admin else 'deactivated'
    log_admin_action(
        user=request.user,
        action='update',
        object_instance=admin_user,
        description=f'{action.capitalize()} admin user: {user.username}',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    return JsonResponse({
        'success': True,
        'message': f'Admin user "{user.username}" {action} successfully.',
        'is_active': admin_user.is_active_admin
    })

@admin_required
@role_required(['Admin', 'Super Admin'])
def audit_logs(request):
    """View audit logs with filtering and pagination"""
    logs = AuditLog.objects.select_related('user', 'content_type').order_by('-timestamp')
    
    # Filters
    user_filter = request.GET.get('user', '')
    action_filter = request.GET.get('action', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)
    
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    if date_from:
        logs = logs.filter(timestamp__gte=date_from)
    
    if date_to:
        logs = logs.filter(timestamp__lte=date_to)
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'action_choices': AuditLog.ACTION_CHOICES,
        'filters': {
            'user': user_filter,
            'action': action_filter,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    
    return render(request, 'admin_panel/audit_logs.html', context)

@admin_required
@role_required(['Admin', 'Super Admin'])
def audit_logs_export(request):
    """Export audit logs to CSV"""
    logs = AuditLog.objects.select_related('user', 'content_type').order_by('-timestamp')
    
    # Apply same filters as audit_logs view
    user_filter = request.GET.get('user', '')
    action_filter = request.GET.get('action', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)
    
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    if date_from:
        logs = logs.filter(timestamp__gte=date_from)
    
    if date_to:
        logs = logs.filter(timestamp__lte=date_to)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'User', 'Action', 'Description', 'IP Address', 'User Agent'])
    
    for log in logs:
        writer.writerow([
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.user.username if log.user else 'System',
            log.get_action_display(),
            log.description,
            log.ip_address or '',
            log.user_agent or ''
        ])
    
    return response

@admin_required
@role_required(['Admin', 'Super Admin'])
def admin_role_list(request):
    """List all admin roles"""
    roles = AdminRole.objects.all().order_by('name')
    
    context = {
        'roles': roles,
    }
    
    return render(request, 'admin_panel/role_list.html', context)

@admin_required
@role_required(['Admin', 'Super Admin'])
def admin_role_create(request):
    """Create new admin role"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description')
            permissions = request.POST.getlist('permissions')
            is_active = request.POST.get('is_active') == 'on'
            
            if not name:
                messages.error(request, 'Role name is required.')
                return redirect('admin_panel:role_create')
            
            role = AdminRole.objects.create(
                name=name,
                description=description,
                is_active=is_active
            )
            
            # Add permissions
            if permissions:
                role.permissions.set(permissions)
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='ROLE_CREATED',
                description=f'Created role: {role.name}',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'Role "{role.name}" created successfully.')
            return redirect('admin_panel:role_list')
            
        except Exception as e:
            messages.error(request, f'Error creating role: {str(e)}')
    
    # Get all permissions
    from django.contrib.auth.models import Permission
    permissions = Permission.objects.all().order_by('content_type__app_label', 'codename')
    
    context = {
        'permissions': permissions,
        'role_choices': AdminRole.ROLE_CHOICES,
    }
    
    return render(request, 'admin_panel/role_create.html', context)

@admin_required
@role_required(['Admin', 'Super Admin'])
def admin_role_edit(request, role_id):
    """Edit admin role"""
    role = get_object_or_404(AdminRole, id=role_id)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description')
            permissions = request.POST.getlist('permissions')
            is_active = request.POST.get('is_active') == 'on'
            
            if not name:
                messages.error(request, 'Role name is required.')
                return redirect('admin_panel:role_edit', role_id=role_id)
            
            role.name = name
            role.description = description
            role.is_active = is_active
            role.save()
            
            # Update permissions
            role.permissions.set(permissions)
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='ROLE_UPDATED',
                description=f'Updated role: {role.name}',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'Role "{role.name}" updated successfully.')
            return redirect('admin_panel:role_list')
            
        except Exception as e:
            messages.error(request, f'Error updating role: {str(e)}')
    
    # Get all permissions
    from django.contrib.auth.models import Permission
    permissions = Permission.objects.all().order_by('content_type__app_label', 'codename')
    
    context = {
        'role': role,
        'permissions': permissions,
        'role_choices': AdminRole.ROLE_CHOICES,
    }
    
    return render(request, 'admin_panel/role_edit.html', context)

@admin_required
@role_required(['superadmin', 'admin', 'analyst'])
def admin_analytics_dashboard(request):
    """Admin analytics dashboard with role-based access"""
    from analytics.views import analytics_dashboard
    
    # Call the original analytics dashboard view
    return analytics_dashboard(request)


@admin_required
@role_required(['superadmin', 'admin', 'analyst'])
def loyalty_management(request):
    """Loyalty program management dashboard"""
    from loyalty.models import LoyaltyAccount, LoyaltyTier, LoyaltyReward, LoyaltyTransaction
    
    # Get loyalty program statistics
    total_accounts = LoyaltyAccount.objects.count()
    active_accounts = LoyaltyAccount.objects.filter(points_balance__gt=0).count()
    total_points_issued = LoyaltyTransaction.objects.filter(transaction_type='earned').aggregate(
        total=Sum('points')
    )['total'] or 0
    total_points_redeemed = LoyaltyTransaction.objects.filter(transaction_type='redeemed').aggregate(
        total=Sum('points')
    )['total'] or 0
    
    # Get tier distribution
    tier_distribution = {}
    for tier in LoyaltyTier.objects.all():
        count = LoyaltyAccount.objects.filter(current_tier=tier).count()
        tier_distribution[tier.display_name] = count
    
    # Get recent transactions
    recent_transactions = LoyaltyTransaction.objects.select_related('account__user').order_by('-created_at')[:10]
    
    # Get active rewards
    active_rewards = LoyaltyReward.objects.filter(is_active=True)
    
    context = {
        'total_accounts': total_accounts,
        'active_accounts': active_accounts,
        'total_points_issued': total_points_issued,
        'total_points_redeemed': total_points_redeemed,
        'tier_distribution': tier_distribution,
        'recent_transactions': recent_transactions,
        'active_rewards': active_rewards,
    }
    
    return render(request, 'admin_panel/loyalty_management.html', context)