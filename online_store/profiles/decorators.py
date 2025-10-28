from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse

def customer_required(view_func):
    """
    Decorator to ensure user is a customer (not an admin)
    Prevents admin users from accessing customer features
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        
        # Check if user is an admin
        try:
            from admin_panel.models import AdminUser
            admin_user = AdminUser.objects.get(user=request.user)
            if admin_user.is_active_admin:
                messages.warning(request, "Admin users cannot access customer features. Please use the admin panel.")
                return redirect('admin_panel:dashboard')
        except:
            # User is not an admin, allow access
            pass
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view
