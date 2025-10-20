#!/usr/bin/env python
"""
Quick Admin Panel Debug Script
"""

import os
import sys
import django
from django.test import Client

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auroramart.settings')
django.setup()

from django.contrib.auth.models import User

from admin_panel.models import AdminUser, AdminRole

def debug_admin():
    """Debug admin authentication"""
    print("🔍 Debugging Admin Authentication...")
    
    client = Client()
    
    # Create or get admin user
    admin_user, created = User.objects.get_or_create(
        username='testadmin',
        defaults={
            'email': 'admin@auroramart.com',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('testpass123')
        admin_user.save()
    
    # Create or get admin role
    admin_role, created = AdminRole.objects.get_or_create(
        name='superadmin',
        defaults={'description': 'Super Administrator'}
    )
    
    # Create or get admin profile
    admin_profile, created = AdminUser.objects.get_or_create(
        user=admin_user,
        defaults={'role': admin_role}
    )
    
    # Ensure the admin user has the proper role
    if not admin_profile.role:
        admin_profile.role = admin_role
        admin_profile.save()
    
    print(f"Admin User: {admin_user.username}")
    print(f"Admin Profile: {admin_profile}")
    print(f"Admin Role: {admin_profile.role}")
    print(f"Is Authenticated: {admin_user.is_authenticated}")
    print(f"Is Staff: {admin_user.is_staff}")
    print(f"Is Superuser: {admin_user.is_superuser}")
    
    # Login
    login_success = client.login(username='testadmin', password='testpass123')
    print(f"Login Success: {login_success}")
    
    if login_success:
        # Test a simple endpoint
        response = client.get('/admin-panel/')
        print(f"Dashboard Response: {response.status_code}")
        
        if response.status_code == 302:
            print(f"Redirect URL: {response.url}")
        
        # Test another endpoint
        response = client.get('/admin-panel/users/')
        print(f"Users Response: {response.status_code}")
        
        if response.status_code == 302:
            print(f"Redirect URL: {response.url}")

if __name__ == "__main__":
    debug_admin()
