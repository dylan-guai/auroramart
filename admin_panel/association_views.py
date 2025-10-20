from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg, F
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
import csv
import json

from item.models import Product, Category, Subcategory, Brand
from checkout.models import Order, OrderItem
from admin_panel.decorators import admin_required, role_required
from admin_panel.models import AuditLog
from core.ml_service import MLService

@admin_required
@role_required(['Admin', 'analyst'])
def association_rules_dashboard(request):
    """Association Rules Dashboard for reviewing and managing AI recommendations"""
    ml_service = MLService()
    
    # Get model status
    model_status = ml_service.get_model_status()
    
    # Get sample rules for review (this would come from the ML model in a real system)
    # For now, we'll simulate some rules based on actual product data
    sample_rules = []
    
    try:
        # Get products that are frequently bought together
        products = Product.objects.filter(is_active=True)[:20]
        
        # Simulate some association rules
        for i, product in enumerate(products[:10]):
            if i < len(products) - 1:
                consequent_product = products[i + 1]
                sample_rules.append({
                    'id': f'rule_{i}',
                    'antecedent': [product.sku],
                    'consequent': [consequent_product.sku],
                    'support': 0.15 + (i * 0.02),  # Simulated support
                    'confidence': 0.65 + (i * 0.03),  # Simulated confidence
                    'lift': 1.2 + (i * 0.1),  # Simulated lift
                    'approved': i % 3 == 0,  # Some approved, some not
                    'created_at': timezone.now() - timedelta(days=i),
                    'antecedent_products': [product],
                    'consequent_products': [consequent_product]
                })
    except Exception as e:
        messages.warning(request, f'Error loading sample rules: {str(e)}')
    
    # Statistics
    total_rules = len(sample_rules)
    approved_rules = len([r for r in sample_rules if r['approved']])
    pending_rules = total_rules - approved_rules
    
    # Filter rules
    status_filter = request.GET.get('status', '')
    if status_filter == 'approved':
        sample_rules = [r for r in sample_rules if r['approved']]
    elif status_filter == 'pending':
        sample_rules = [r for r in sample_rules if not r['approved']]
    
    # Pagination
    paginator = Paginator(sample_rules, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'model_status': model_status,
        'total_rules': total_rules,
        'approved_rules': approved_rules,
        'pending_rules': pending_rules,
        'status_filter': status_filter,
    }
    
    return render(request, 'admin_panel/association_rules_dashboard.html', context)

@admin_required
@role_required(['Admin', 'analyst'])
def association_rule_detail(request, rule_id):
    """Detailed view of a specific association rule"""
    # In a real system, this would fetch the actual rule from the ML model
    # For now, we'll simulate it
    
    ml_service = MLService()
    model_status = ml_service.get_model_status()
    
    # Simulate rule data
    rule_data = {
        'id': rule_id,
        'antecedent': ['SKU001', 'SKU002'],
        'consequent': ['SKU003'],
        'support': 0.18,
        'confidence': 0.72,
        'lift': 1.35,
        'approved': False,
        'created_at': timezone.now() - timedelta(days=5),
        'last_used': timezone.now() - timedelta(hours=2),
        'usage_count': 45,
        'success_rate': 0.68
    }
    
    # Get actual products
    antecedent_products = Product.objects.filter(sku__in=rule_data['antecedent'])
    consequent_products = Product.objects.filter(sku__in=rule_data['consequent'])
    
    # Get affected products (products that would be recommended)
    affected_products = consequent_products
    
    context = {
        'rule': rule_data,
        'antecedent_products': antecedent_products,
        'consequent_products': consequent_products,
        'affected_products': affected_products,
        'model_status': model_status,
    }
    
    return render(request, 'admin_panel/association_rule_detail.html', context)

@admin_required
@role_required(['Admin', 'analyst'])
def approve_association_rule(request, rule_id):
    """Approve an association rule for use in recommendations"""
    if request.method == 'POST':
        try:
            # In a real system, this would update the rule status in the ML model
            # For now, we'll just log the action
            
            AuditLog.objects.create(
                user=request.user,
                action='ASSOCIATION_RULE_APPROVED',
                description=f'Approved association rule: {rule_id}'
            )
            
            messages.success(request, f'Association rule {rule_id} has been approved.')
            return redirect('admin_panel:association_rules_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error approving rule: {str(e)}')
    
    return redirect('admin_panel:association_rules_dashboard')

@admin_required
@role_required(['Admin', 'analyst'])
def reject_association_rule(request, rule_id):
    """Reject an association rule"""
    if request.method == 'POST':
        try:
            reason = request.POST.get('reason', 'No reason provided')
            
            # In a real system, this would update the rule status in the ML model
            # For now, we'll just log the action
            
            AuditLog.objects.create(
                user=request.user,
                action='ASSOCIATION_RULE_REJECTED',
                description=f'Rejected association rule: {rule_id}. Reason: {reason}'
            )
            
            messages.success(request, f'Association rule {rule_id} has been rejected.')
            return redirect('admin_panel:association_rules_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error rejecting rule: {str(e)}')
    
    return redirect('admin_panel:association_rules_dashboard')

@admin_required
@role_required(['Admin', 'analyst'])
def association_rules_export(request):
    """Export association rules to CSV"""
    # Get sample rules (in real system, this would come from ML model)
    sample_rules = []
    
    try:
        products = Product.objects.filter(is_active=True)[:10]
        for i, product in enumerate(products[:5]):
            if i < len(products) - 1:
                consequent_product = products[i + 1]
                sample_rules.append({
                    'id': f'rule_{i}',
                    'antecedent': product.sku,
                    'consequent': consequent_product.sku,
                    'support': 0.15 + (i * 0.02),
                    'confidence': 0.65 + (i * 0.03),
                    'lift': 1.2 + (i * 0.1),
                    'approved': i % 3 == 0,
                    'created_at': timezone.now() - timedelta(days=i)
                })
    except Exception as e:
        messages.error(request, f'Error generating export data: {str(e)}')
        return redirect('admin_panel:association_rules_dashboard')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="association_rules_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Rule ID', 'Antecedent SKU', 'Consequent SKU', 'Support', 'Confidence', 'Lift', 'Approved', 'Created At'
    ])
    
    for rule in sample_rules:
        writer.writerow([
            rule['id'],
            rule['antecedent'],
            rule['consequent'],
            f"{rule['support']:.3f}",
            f"{rule['confidence']:.3f}",
            f"{rule['lift']:.3f}",
            rule['approved'],
            rule['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response

@admin_required
@role_required(['Admin', 'analyst'])
def ai_recommendations_analytics(request):
    """Analytics for AI recommendations performance"""
    # Get recommendation performance data
    # In a real system, this would come from tracking recommendation clicks and conversions
    
    # Simulate some analytics data
    total_recommendations_shown = 1250
    total_clicks = 187
    total_add_to_cart = 45
    total_purchases = 23
    
    analytics_data = {
        'total_recommendations_shown': total_recommendations_shown,
        'total_clicks': total_clicks,
        'total_add_to_cart': total_add_to_cart,
        'total_purchases': total_purchases,
        'click_through_rate': (total_clicks / total_recommendations_shown * 100) if total_recommendations_shown > 0 else 0,
        'conversion_rate': (total_purchases / total_clicks * 100) if total_clicks > 0 else 0,
        'add_to_cart_rate': (total_add_to_cart / total_clicks * 100) if total_clicks > 0 else 0,
        'average_order_value_lift': 8.0
    }
    
    # Get top performing rules
    top_rules = []
    try:
        products = Product.objects.filter(is_active=True)[:10]
        for i, product in enumerate(products[:5]):
            if i < len(products) - 1:
                consequent_product = products[i + 1]
                top_rules.append({
                    'rule_id': f'rule_{i}',
                    'antecedent': product.name,
                    'consequent': consequent_product.name,
                    'clicks': 25 - i * 3,
                    'conversions': 8 - i,
                    'ctr': 0.18 - i * 0.02,
                    'conversion_rate': 0.15 - i * 0.01
                })
    except Exception as e:
        messages.warning(request, f'Error loading analytics data: {str(e)}')
    
    context = {
        'analytics_data': analytics_data,
        'top_rules': top_rules,
    }
    
    return render(request, 'admin_panel/ai_recommendations_analytics.html', context)

@admin_required
@role_required(['Admin', 'analyst'])
def retrain_association_rules(request):
    """Retrain association rules with new data"""
    if request.method == 'POST':
        try:
            # In a real system, this would trigger retraining of the ML model
            # For now, we'll just log the action
            
            AuditLog.objects.create(
                user=request.user,
                action='ASSOCIATION_RULES_RETRAIN',
                description='Manual retraining requested for association rules'
            )
            
            messages.success(request, 'Association rules retraining has been initiated. This process may take several minutes.')
            return redirect('admin_panel:association_rules_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error initiating retraining: {str(e)}')
    
    return redirect('admin_panel:association_rules_dashboard')
