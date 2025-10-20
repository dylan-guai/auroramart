#!/usr/bin/env python
"""
Comprehensive Admin Panel Test Script
Tests all admin panel endpoints and functionality
"""

import os
import sys
import django
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auroramart.settings')
django.setup()

from django.contrib.auth.models import User
from admin_panel.models import AdminUser, AdminRole, AuditLog, LoginAttempt, SessionSecurity
from item.models import Product, Category, Subcategory, Brand
from checkout.models import Order, OrderItem
from profiles.models import Profile

def test_admin_panel():
    """Comprehensive test of admin panel functionality"""
    print("🔍 Starting Comprehensive Admin Panel Test...")
    
    client = Client()
    
    # Test results
    results = {
        'passed': 0,
        'failed': 0,
        'errors': []
    }
    
    def test_endpoint(name, url, expected_status=200, method='GET', data=None):
        """Test a single endpoint"""
        try:
            if method == 'GET':
                response = client.get(url)
            elif method == 'POST':
                response = client.post(url, data or {})
            
            if response.status_code == expected_status:
                print(f"✅ {name}: {response.status_code}")
                results['passed'] += 1
                return True
            else:
                print(f"❌ {name}: Expected {expected_status}, got {response.status_code}")
                results['failed'] += 1
                results['errors'].append(f"{name}: Expected {expected_status}, got {response.status_code}")
                return False
        except Exception as e:
            print(f"💥 {name}: Exception - {str(e)}")
            results['failed'] += 1
            results['errors'].append(f"{name}: Exception - {str(e)}")
            return False
    
    # Test 1: Admin Login Page
    print("\n📋 Testing Admin Authentication...")
    test_endpoint("Admin Login Page", "/admin-panel/login/")
    
    # Test 2: Admin Dashboard (should redirect to login)
    test_endpoint("Admin Dashboard (unauthenticated)", "/admin-panel/", expected_status=302)
    
    # Test 3: Create test admin user and login
    print("\n👤 Setting up test admin user...")
    try:
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
        
        print("✅ Test admin user created/verified")
        
        # Login
        login_success = client.login(username='testadmin', password='testpass123')
        if login_success:
            print("✅ Admin login successful")
        else:
            print("❌ Admin login failed")
            return results
            
    except Exception as e:
        print(f"💥 Error setting up admin user: {str(e)}")
        return results
    
    # Test 4: Authenticated Admin Endpoints
    print("\n🔐 Testing Authenticated Admin Endpoints...")
    
    # Dashboard
    test_endpoint("Admin Dashboard", "/admin-panel/")
    
    # User Management
    test_endpoint("Admin User List", "/admin-panel/users/")
    test_endpoint("Admin User Create", "/admin-panel/users/create/")
    
    # Product Management
    test_endpoint("Product List", "/admin-panel/products/")
    test_endpoint("Product Performance", "/admin-panel/products/performance/")
    
    # Category Management
    test_endpoint("Category List", "/admin-panel/categories/")
    test_endpoint("Category Create", "/admin-panel/categories/create/")
    
    # Inventory Management
    test_endpoint("Inventory Overview", "/admin-panel/inventory/")
    test_endpoint("Stock Adjustments", "/admin-panel/inventory/adjustments/")
    test_endpoint("Reorder Suggestions", "/admin-panel/inventory/reorder-suggestions/")
    
    # Customer Management
    test_endpoint("Customer List", "/admin-panel/customers/")
    test_endpoint("AI Predictions Dashboard", "/admin-panel/ai-predictions/")
    
    # AI Analytics
    test_endpoint("AI Recommendations Analytics", "/admin-panel/ai-analytics/")
    
    # Security Settings
    test_endpoint("Security Settings", "/admin-panel/security/")
    
    # Test 5: Test specific product detail (if products exist)
    print("\n📦 Testing Product Detail...")
    try:
        product = Product.objects.first()
        if product:
            test_endpoint(f"Product Detail ({product.id})", f"/admin-panel/products/{product.id}/")
            test_endpoint(f"Product Edit ({product.id})", f"/admin-panel/products/{product.id}/edit/")
        else:
            print("⚠️ No products found to test product detail")
    except Exception as e:
        print(f"💥 Error testing product detail: {str(e)}")
    
    # Test 6: Test category edit (if categories exist)
    print("\n📂 Testing Category Edit...")
    try:
        category = Category.objects.first()
        if category:
            test_endpoint(f"Category Edit ({category.id})", f"/admin-panel/categories/{category.id}/edit/")
        else:
            print("⚠️ No categories found to test category edit")
    except Exception as e:
        print(f"💥 Error testing category edit: {str(e)}")
    
    # Test 7: Test customer detail (if customers exist)
    print("\n👥 Testing Customer Detail...")
    try:
        customer = Profile.objects.first()
        if customer:
            test_endpoint(f"Customer Detail ({customer.id})", f"/admin-panel/customers/{customer.id}/")
            test_endpoint(f"Customer Orders ({customer.id})", f"/admin-panel/customers/{customer.id}/orders/")
        else:
            print("⚠️ No customers found to test customer detail")
    except Exception as e:
        print(f"💥 Error testing customer detail: {str(e)}")
    
    # Test 8: Test AJAX endpoints
    print("\n🔄 Testing AJAX Endpoints...")
    
    # Test admin user toggle
    try:
        admin_user_to_toggle = AdminUser.objects.exclude(user=admin_user).first()
        if admin_user_to_toggle:
            test_endpoint(
                f"Toggle Admin User ({admin_user_to_toggle.id})",
                f"/admin-panel/users/{admin_user_to_toggle.id}/toggle/",
                method='POST',
                data={'is_active': 'true'}
            )
        else:
            print("⚠️ No other admin users found to test toggle")
    except Exception as e:
        print(f"💥 Error testing admin user toggle: {str(e)}")
    
    # Test 9: Test logout
    print("\n🚪 Testing Logout...")
    test_endpoint("Admin Logout", "/admin-panel/logout/", method='POST')
    
    # Test 10: Test unauthenticated access after logout
    print("\n🔒 Testing Unauthenticated Access...")
    test_endpoint("Admin Dashboard (after logout)", "/admin-panel/", expected_status=302)
    
    # Summary
    print(f"\n📊 Test Summary:")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    
    if results['errors']:
        print(f"\n💥 Errors:")
        for error in results['errors']:
            print(f"   - {error}")
    
    success_rate = (results['passed'] / (results['passed'] + results['failed'])) * 100
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("🎉 Admin Panel is working excellently!")
    elif success_rate >= 80:
        print("✅ Admin Panel is working well with minor issues")
    elif success_rate >= 70:
        print("⚠️ Admin Panel has some issues that need attention")
    else:
        print("🚨 Admin Panel has significant issues that need immediate attention")
    
    return results

if __name__ == "__main__":
    test_admin_panel()
