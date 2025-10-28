from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg, F
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
import csv

from online_store.profiles.models import Profile, Wishlist
from online_store.checkout.models import Order
from online_store.item.models import Product, Category, Subcategory
from admin_panel.decorators import admin_required, role_required
from admin_panel.models import AuditLog
from online_store.core.ml_service import MLService

@admin_required
@role_required(['Admin', 'CRM', 'analyst'])
def customer_list(request):
    """Customer list with filtering and search"""
    customers = Profile.objects.select_related('user').prefetch_related('order_set').all()
    
    # Search and filters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    gender_filter = request.GET.get('gender', '')
    income_filter = request.GET.get('income', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if search_query:
        customers = customers.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    if category_filter:
        customers = customers.filter(predicted_category_id=category_filter)
    
    if gender_filter:
        customers = customers.filter(gender=gender_filter)
    
    if income_filter:
        customers = customers.filter(monthly_income_sgd=income_filter)
    
    if date_from:
        customers = customers.filter(user__date_joined__gte=date_from)
    
    if date_to:
        customers = customers.filter(user__date_joined__lte=date_to)
    
    # Annotate with order statistics
    customers = customers.annotate(
        total_orders=Count('order'),
        total_spent=Sum('order__total_amount'),
        avg_order_value=Avg('order__total_amount'),
        last_order_date=F('order__created_at')
    ).order_by('-user__date_joined')
    
    # Pagination
    paginator = Paginator(customers, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    categories = Category.objects.all()
    genders = Profile.GENDER_CHOICES
    income_ranges = Profile.INCOME_CHOICES
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'gender_filter': gender_filter,
        'income_filter': income_filter,
        'date_from': date_from,
        'date_to': date_to,
        'categories': categories,
        'genders': genders,
        'income_ranges': income_ranges,
    }
    
    return render(request, 'admin_panel/customer_list.html', context)

@admin_required
@role_required(['Admin', 'CRM', 'analyst'])
def customer_detail(request, customer_id):
    """Customer profile 360 view"""
    customer = get_object_or_404(Profile, id=customer_id)
    
    # Get customer orders
    orders = Order.objects.filter(user=customer.user).order_by('-created_at')
    
    # Calculate metrics
    total_orders = orders.count()
    total_spent = orders.aggregate(total=Sum('total_amount'))['total'] or 0
    avg_order_value = orders.aggregate(avg=Avg('total_amount'))['avg'] or 0
    last_order = orders.first()
    
    # Get wishlist items
    wishlist_items = Wishlist.objects.filter(user=customer.user).select_related('product')
    
    # Get AI prediction
    ml_service = MLService()
    predicted_category = None
    prediction_confidence = None
    
    if customer.is_onboarding_complete:
        try:
            prediction_result = ml_service.predict_preferred_category(customer)
            if prediction_result['success']:
                predicted_category = prediction_result['predicted_category']
                prediction_confidence = prediction_result.get('confidence', 0)
        except Exception as e:
            messages.warning(request, f'AI prediction failed: {str(e)}')
    
    # Get order history for chart
    order_history = orders.values('created_at__date').annotate(
        daily_total=Sum('total_amount'),
        daily_orders=Count('order_id')
    ).order_by('created_at__date')[:30]
    
    context = {
        'customer': customer,
        'orders': orders[:10],  # Recent orders
        'total_orders': total_orders,
        'total_spent': total_spent,
        'avg_order_value': avg_order_value,
        'last_order': last_order,
        'wishlist_items': wishlist_items[:10],
        'predicted_category': predicted_category,
        'prediction_confidence': prediction_confidence,
        'order_history': order_history,
    }
    
    return render(request, 'admin_panel/customer_detail.html', context)

@admin_required
@role_required(['Admin', 'CRM', 'analyst'])
def customer_orders(request, customer_id):
    """Customer order history"""
    customer = get_object_or_404(Profile, id=customer_id)
    orders = Order.objects.filter(user=customer.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'customer': customer,
        'page_obj': page_obj,
    }
    
    return render(request, 'admin_panel/customer_orders.html', context)

@admin_required
@role_required(['Admin', 'analyst'])
def ai_predictions_dashboard(request):
    """AI Predictions Dashboard"""
    # Get prediction statistics
    customers_with_predictions = Profile.objects.filter(
        is_onboarding_complete=True
    ).exclude(predicted_category_id__isnull=True)
    
    # Category distribution
    category_distribution = customers_with_predictions.values('predicted_category_id').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Recent predictions
    recent_predictions = customers_with_predictions.order_by('-updated_at')[:20]
    
    # Prediction accuracy (simplified - compare predicted vs actual dominant category)
    accuracy_data = []
    for customer in customers_with_predictions[:100]:  # Sample for performance
        orders = Order.objects.filter(user=customer.user)
        if orders.exists():
            # Get most ordered category
            orderitem = orders.values('orderitem__product__category__name').annotate(
                total_quantity=Sum('orderitem__quantity')
            ).order_by('-total_quantity').first()
            
            if orderitem:
                actual_category = orderitem['orderitem__product__category__name']
                predicted_category = customer.predicted_category
                accuracy_data.append({
                    'customer': customer,
                    'predicted': predicted_category,
                    'actual': actual_category,
                    'correct': predicted_category == actual_category
                })
    
    accuracy_rate = sum(1 for item in accuracy_data if item['correct']) / len(accuracy_data) if accuracy_data else 0
    
    total_customers = Profile.objects.count()
    customers_with_predictions_count = customers_with_predictions.count()
    prediction_coverage = (customers_with_predictions_count / total_customers * 100) if total_customers > 0 else 0
    
    context = {
        'total_customers': total_customers,
        'customers_with_predictions': customers_with_predictions_count,
        'prediction_coverage': prediction_coverage,
        'category_distribution': category_distribution,
        'recent_predictions': recent_predictions,
        'accuracy_data': accuracy_data[:20],  # Show sample
        'accuracy_rate': accuracy_rate,
    }
    
    return render(request, 'admin_panel/ai_predictions_dashboard.html', context)

@admin_required
@role_required(['Admin', 'analyst'])
def rescore_customer(request, customer_id):
    """Re-score a single customer"""
    customer = get_object_or_404(Profile, id=customer_id)
    
    if request.method == 'POST':
        ml_service = MLService()
        
        try:
            result = ml_service.predict_preferred_category(customer)
            if result['success']:
                customer.predicted_category = result['predicted_category']
                customer.prediction_updated_at = timezone.now()
                customer.save()
                
                # Log the action
                AuditLog.objects.create(
                    user=request.user,
                    action='RESCORE_CUSTOMER',
                    description=f'Re-scored customer {customer.user.email}. New prediction: {result["predicted_category"]}'
                )
                
                messages.success(request, f'Customer re-scored successfully. New prediction: {result["predicted_category"]}')
            else:
                messages.error(request, 'Failed to re-score customer')
        except Exception as e:
            messages.error(request, f'Error re-scoring customer: {str(e)}')
    
    return redirect('admin_panel:customer_detail', customer_id=customer_id)

@admin_required
@role_required(['Admin', 'analyst'])
def batch_rescore_customers(request):
    """Batch re-score customers"""
    if request.method == 'POST':
        customers = Profile.objects.filter(is_onboarding_complete=True)
        ml_service = MLService()
        
        success_count = 0
        error_count = 0
        
        for customer in customers:
            try:
                result = ml_service.predict_preferred_category(customer)
                if result['success']:
                    customer.predicted_category = result['predicted_category']
                    customer.prediction_updated_at = timezone.now()
                    customer.save()
                    success_count += 1
                else:
                    error_count += 1
            except Exception:
                error_count += 1
        
        # Log the batch action
        AuditLog.objects.create(
            user=request.user,
            action='BATCH_RESCORE',
            description=f'Batch re-scored {success_count} customers. Success: {success_count}, Errors: {error_count}'
        )
        
        messages.success(request, f'Batch re-scoring completed. Success: {success_count}, Errors: {error_count}')
    
    return redirect('admin_panel:ai_predictions_dashboard')

@admin_required
@role_required(['Admin', 'CRM', 'analyst'])
def export_customers(request):
    """Export customer data to CSV"""
    customers = Profile.objects.select_related('user').prefetch_related('order_set').all()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="customers_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Email', 'First Name', 'Last Name', 'Gender', 'Age', 'Income Range',
        'Employment Status', 'Education', 'Predicted Category', 'Total Orders',
        'Total Spent', 'Avg Order Value', 'Last Order Date', 'Date Joined'
    ])
    
    for customer in customers:
        orders = customer.order_set.all()
        total_orders = orders.count()
        total_spent = orders.aggregate(total=Sum('total_amount'))['total'] or 0
        avg_order_value = orders.aggregate(avg=Avg('total_amount'))['avg'] or 0
        last_order = orders.order_by('-created_at').first()
        
        writer.writerow([
            customer.user.email,
            customer.user.first_name,
            customer.user.last_name,
            customer.get_gender_display(),
            customer.age,
            customer.get_monthly_income_sgd_display(),
            customer.get_employment_status_display(),
            customer.get_education_display(),
            customer.predicted_category,
            total_orders,
            total_spent,
            avg_order_value,
            last_order.created_at if last_order else '',
            customer.user.date_joined.strftime('%Y-%m-%d')
        ])
    
    return response
