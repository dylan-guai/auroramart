from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from admin_panel.models import SessionSecurity, AdminUser
from admin_panel.utils import get_client_ip, log_admin_action

@login_required
def extend_session(request):
    """Extend user session if still active"""
    if request.method == 'POST':
        try:
            admin_user = AdminUser.objects.get(user=request.user)
            
            # Update session security
            session_security = SessionSecurity.objects.get(
                user=request.user,
                session_key=request.session.session_key
            )
            
            # Check if session is still valid
            if session_security.is_expired:
                return JsonResponse({'success': False, 'message': 'Session expired'})
            
            # Extend session
            session_security.last_activity = timezone.now()
            session_security.save()
            
            return JsonResponse({
                'success': True, 
                'message': 'Session extended',
                'expires_at': session_security.expires_at.isoformat()
            })
            
        except (AdminUser.DoesNotExist, SessionSecurity.DoesNotExist):
            return JsonResponse({'success': False, 'message': 'Invalid session'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def session_status(request):
    """Get current session status"""
    try:
        admin_user = AdminUser.objects.get(user=request.user)
        session_security = SessionSecurity.objects.get(
            user=request.user,
            session_key=request.session.session_key
        )
        
        return JsonResponse({
            'success': True,
            'is_expired': session_security.is_expired,
            'expires_at': session_security.expires_at.isoformat(),
            'last_activity': session_security.last_activity.isoformat(),
            'time_remaining': (session_security.expires_at - timezone.now()).total_seconds()
        })
        
    except (AdminUser.DoesNotExist, SessionSecurity.DoesNotExist):
        return JsonResponse({'success': False, 'message': 'Invalid session'})

@login_required
def logout_all_sessions(request):
    """Logout user from all sessions"""
    if request.method == 'POST':
        try:
            admin_user = AdminUser.objects.get(user=request.user)
            
            # Delete all session security records for this user
            SessionSecurity.objects.filter(user=request.user).delete()
            
            # Log the action
            log_admin_action(
                user=request.user,
                action='LOGOUT_ALL_SESSIONS',
                description='Logged out from all sessions',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Logout current session
            logout(request)
            
            messages.success(request, 'You have been logged out from all sessions.')
            return redirect('admin_panel:login')
            
        except AdminUser.DoesNotExist:
            messages.error(request, 'Admin user not found.')
            return redirect('admin_panel:dashboard')
        except Exception as e:
            messages.error(request, f'Error logging out all sessions: {str(e)}')
            return redirect('admin_panel:dashboard')
    
    return redirect('admin_panel:dashboard')

@login_required
def change_password(request):
    """Change password with security checks"""
    if request.method == 'POST':
        try:
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # Validate inputs
            if not all([current_password, new_password, confirm_password]):
                messages.error(request, 'All fields are required.')
                return redirect('admin_panel:password_change')
            
            if new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
                return redirect('admin_panel:password_change')
            
            # Check current password
            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
                return redirect('admin_panel:password_change')
            
            # Validate new password strength
            if len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return redirect('admin_panel:password_change')
            
            # Change password
            request.user.set_password(new_password)
            request.user.save()
            
            # Log the action
            log_admin_action(
                user=request.user,
                action='PASSWORD_CHANGED',
                description='Password changed successfully',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Logout all other sessions for security
            SessionSecurity.objects.filter(user=request.user).exclude(
                session_key=request.session.session_key
            ).delete()
            
            messages.success(request, 'Password changed successfully. You have been logged out from all other sessions.')
            return redirect('admin_panel:login')
            
        except Exception as e:
            messages.error(request, f'Error changing password: {str(e)}')
    
    return render(request, 'admin_panel/password_change.html')

@login_required
def security_settings(request):
    """Security settings page"""
    try:
        admin_user = AdminUser.objects.get(user=request.user)
        
        # Get active sessions
        active_sessions = SessionSecurity.objects.filter(
            user=request.user,
            expires_at__gt=timezone.now()
        ).order_by('-last_activity')
        
        # Get login attempts
        from admin_panel.models import LoginAttempt
        recent_attempts = LoginAttempt.objects.filter(
            username=request.user.username
        ).order_by('-timestamp')[:10]
        
        context = {
            'admin_user': admin_user,
            'active_sessions': active_sessions,
            'recent_attempts': recent_attempts,
        }
        
        return render(request, 'admin_panel/security_settings.html', context)
        
    except AdminUser.DoesNotExist:
        messages.error(request, 'Admin user not found.')
        return redirect('admin_panel:dashboard')

@csrf_exempt
@require_http_methods(["POST"])
def heartbeat(request):
    """Heartbeat endpoint to keep session alive"""
    if request.user.is_authenticated:
        try:
            admin_user = AdminUser.objects.get(user=request.user)
            session_security = SessionSecurity.objects.get(
                user=request.user,
                session_key=request.session.session_key
            )
            
            # Update last activity
            session_security.last_activity = timezone.now()
            session_security.save()
            
            return JsonResponse({'success': True, 'timestamp': timezone.now().isoformat()})
            
        except (AdminUser.DoesNotExist, SessionSecurity.DoesNotExist):
            pass
    
    return JsonResponse({'success': False, 'message': 'Session not found'})
