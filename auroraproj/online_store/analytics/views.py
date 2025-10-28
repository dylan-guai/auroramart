from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

# Import admin panel decorators
from admin_panel.decorators import admin_required, role_required

from .models import (
    AnalyticsDashboard, AnalyticsWidget, BusinessMetrics,
    CustomerAnalytics, ProductAnalytics, MarketingAnalytics,
    AIPerformanceMetrics, AnalyticsReport
)
from online_store.checkout.models import Order, OrderItem
from online_store.profiles.models import Profile
from online_store.item.models import Product, Category, ProductReview
from online_store.loyalty.models import LoyaltyAccount, LoyaltyTransaction


@admin_required
@role_required(['superadmin', 'admin', 'analyst'])
def analytics_dashboard(request):
    """Main analytics dashboard for admins"""
    # Get date range (default to last 30 days)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Get date range from request
    if request.GET.get('start_date'):
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
    if request.GET.get('end_date'):
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
    
    # Get business metrics
    business_metrics = BusinessMetrics.objects.filter(
        date__range=[start_date, end_date]
    ).order_by('-date')
    
    # Get customer analytics
    customer_analytics = CustomerAnalytics.objects.filter(
        date__range=[start_date, end_date]
    ).order_by('-date')
    
    # Get product analytics
    product_analytics = ProductAnalytics.objects.filter(
        date__range=[start_date, end_date]
    ).order_by('-date')
    
    # Get marketing analytics
    marketing_analytics = MarketingAnalytics.objects.filter(
        date__range=[start_date, end_date]
    ).order_by('-date')
    
    # Get AI performance metrics
    ai_metrics = AIPerformanceMetrics.objects.filter(
        date__range=[start_date, end_date]
    ).order_by('-date')
    
    # Calculate summary metrics
    summary_metrics = calculate_summary_metrics(start_date, end_date)
    
    # Get chart data
    chart_data = get_chart_data(start_date, end_date)
    
    # Structure metrics for template
    revenue_metrics = {
        'total_revenue': summary_metrics.get('total_revenue', 0),
        'growth_percentage': 15.2,  # Placeholder - calculate from previous period
    }
    
    order_metrics = {
        'total_orders': summary_metrics.get('total_orders', 0),
        'growth_percentage': 8.5,  # Placeholder - calculate from previous period
        'average_order_value': summary_metrics.get('avg_order_value', 0),
        'aov_growth_percentage': 12.3,  # Placeholder - calculate from previous period
    }
    
    customer_metrics = {
        'active_customers': summary_metrics.get('total_customers', 0),
        'growth_percentage': 5.7,  # Placeholder - calculate from previous period
    }
    
    product_metrics = {
        'total_products': summary_metrics.get('products_sold', 0),
        'growth_percentage': 18.9,  # Placeholder - calculate from previous period
    }
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'date_range': f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}",
        'business_metrics': business_metrics,
        'customer_analytics': customer_analytics,
        'product_analytics': product_analytics,
        'marketing_analytics': marketing_analytics,
        'ai_metrics': ai_metrics,
        'summary_metrics': summary_metrics,
        'chart_data': chart_data,
        'revenue_metrics': revenue_metrics,
        'order_metrics': order_metrics,
        'customer_metrics': customer_metrics,
        'product_metrics': product_metrics,
    }
    
    return render(request, 'analytics/dashboard.html', context)


@staff_member_required
def analytics_revenue(request):
    """Revenue analytics page"""
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date'):
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
    if request.GET.get('end_date'):
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
    
    # Get revenue data
    revenue_data = get_revenue_analytics(start_date, end_date)
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'revenue_data': revenue_data,
    }
    
    return render(request, 'analytics/revenue.html', context)


@staff_member_required
def analytics_customers(request):
    """Customer analytics page"""
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date'):
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
    if request.GET.get('end_date'):
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
    
    # Get customer data
    customer_data = get_customer_analytics(start_date, end_date)
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'customer_data': customer_data,
    }
    
    return render(request, 'analytics/customers.html', context)


@staff_member_required
def analytics_products(request):
    """Product analytics page"""
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date'):
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
    if request.GET.get('end_date'):
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
    
    # Get product data
    product_data = get_product_analytics(start_date, end_date)
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'product_data': product_data,
    }
    
    return render(request, 'analytics/products.html', context)


@staff_member_required
def analytics_marketing(request):
    """Marketing analytics page"""
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date'):
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
    if request.GET.get('end_date'):
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
    
    # Get marketing data
    marketing_data = get_marketing_analytics(start_date, end_date)
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'marketing_data': marketing_data,
    }
    
    return render(request, 'analytics/marketing.html', context)


@staff_member_required
def analytics_ai_performance(request):
    """AI/ML performance analytics page"""
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date'):
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
    if request.GET.get('end_date'):
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
    
    # Get AI performance data
    ai_data = get_ai_performance_analytics(start_date, end_date)
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'ai_data': ai_data,
    }
    
    return render(request, 'analytics/ai_performance.html', context)


def analytics_api_data(request):
    """API endpoint for analytics data"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Staff access required'}, status=403)
    
    chart_type = request.GET.get('chart_type', 'revenue')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        start_date = timezone.now().date() - timedelta(days=30)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        end_date = timezone.now().date()
    
    data = {}
    
    if chart_type == 'revenue':
        data = get_revenue_chart_data(start_date, end_date)
    elif chart_type == 'orders':
        data = get_orders_chart_data(start_date, end_date)
    elif chart_type == 'customers':
        data = get_customers_chart_data(start_date, end_date)
    elif chart_type == 'products':
        data = get_products_chart_data(start_date, end_date)
    elif chart_type == 'ai_performance':
        data = get_ai_chart_data(start_date, end_date)
    
    return JsonResponse(data)


# Helper functions for analytics calculations

def calculate_summary_metrics(start_date, end_date):
    """Calculate summary metrics for the dashboard"""
    # Revenue metrics
    total_revenue = Order.objects.filter(
        created_at__date__range=[start_date, end_date],
        status='delivered'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Order metrics
    total_orders = Order.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).count()
    
    completed_orders = Order.objects.filter(
        created_at__date__range=[start_date, end_date],
        status='delivered'
    ).count()
    
    avg_order_value = Order.objects.filter(
        created_at__date__range=[start_date, end_date],
        status='delivered'
    ).aggregate(avg=Avg('total_amount'))['avg'] or 0
    
    # Customer metrics
    new_customers = Profile.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).count()
    
    total_customers = Profile.objects.count()
    
    # Product metrics
    products_sold = OrderItem.objects.filter(
        order__created_at__date__range=[start_date, end_date],
        order__status='delivered'
    ).aggregate(total=Sum('quantity'))['total'] or 0
    
    # AI metrics
    ai_revenue = Order.objects.filter(
        created_at__date__range=[start_date, end_date],
        status='delivered'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    return {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'avg_order_value': avg_order_value,
        'new_customers': new_customers,
        'total_customers': total_customers,
        'products_sold': products_sold,
        'ai_revenue': ai_revenue,
        'conversion_rate': (completed_orders / total_orders * 100) if total_orders > 0 else 0,
        'customer_growth_rate': (new_customers / total_customers * 100) if total_customers > 0 else 0,
    }


def get_chart_data(start_date, end_date):
    """Get data for various charts"""
    # Revenue over time
    revenue_data = []
    current_date = start_date
    while current_date <= end_date:
        daily_revenue = Order.objects.filter(
            created_at__date=current_date,
            status='delivered'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        revenue_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'revenue': float(daily_revenue)
        })
        current_date += timedelta(days=1)
    
    # Orders over time
    orders_data = []
    current_date = start_date
    while current_date <= end_date:
        daily_orders = Order.objects.filter(
            created_at__date=current_date
        ).count()
        
        orders_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'orders': daily_orders
        })
        current_date += timedelta(days=1)
    
    # Top categories
    top_categories = Category.objects.annotate(
        revenue=Sum('products__orderitem__order__total_amount', 
                   filter=Q(products__orderitem__order__status='delivered',
                           products__orderitem__order__created_at__date__range=[start_date, end_date]))
    ).order_by('-revenue')[:5]
    
    category_data = []
    for category in top_categories:
        category_data.append({
            'name': category.name,
            'revenue': float(category.revenue or 0)
        })
    
    return {
        'revenue_over_time': revenue_data,
        'orders_over_time': orders_data,
        'top_categories': category_data,
    }


def get_revenue_analytics(start_date, end_date):
    """Get detailed revenue analytics"""
    # Revenue by category
    revenue_by_category = Category.objects.annotate(
        revenue=Sum('products__orderitem__order__total_amount',
                   filter=Q(products__orderitem__order__status='delivered',
                           products__orderitem__order__created_at__date__range=[start_date, end_date]))
    ).order_by('-revenue')
    
    # Revenue by day of week
    revenue_by_day = []
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for i, day in enumerate(days):
        day_revenue = Order.objects.filter(
            created_at__week_day=i+2,  # Django uses 1=Sunday, 2=Monday, etc.
            created_at__date__range=[start_date, end_date],
            status='delivered'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        revenue_by_day.append({
            'day': day,
            'revenue': float(day_revenue)
        })
    
    # Revenue by hour
    revenue_by_hour = []
    for hour in range(24):
        hour_revenue = Order.objects.filter(
            created_at__hour=hour,
            created_at__date__range=[start_date, end_date],
            status='delivered'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        revenue_by_hour.append({
            'hour': hour,
            'revenue': float(hour_revenue)
        })
    
    return {
        'revenue_by_category': revenue_by_category,
        'revenue_by_day': revenue_by_day,
        'revenue_by_hour': revenue_by_hour,
    }


def get_customer_analytics(start_date, end_date):
    """Get detailed customer analytics"""
    # Customer segments
    high_value_customers = Profile.objects.annotate(
        total_spent=Sum('user__order__total_amount',
                       filter=Q(user__order__status='delivered',
                               user__order__created_at__date__range=[start_date, end_date]))
    ).filter(total_spent__gte=1000).count()
    
    medium_value_customers = Profile.objects.annotate(
        total_spent=Sum('user__order__total_amount',
                       filter=Q(user__order__status='delivered',
                               user__order__created_at__date__range=[start_date, end_date]))
    ).filter(total_spent__gte=100, total_spent__lt=1000).count()
    
    low_value_customers = Profile.objects.annotate(
        total_spent=Sum('user__order__total_amount',
                       filter=Q(user__order__status='delivered',
                               user__order__created_at__date__range=[start_date, end_date]))
    ).filter(total_spent__lt=100).count()
    
    # Customer lifetime value
    avg_clv = Profile.objects.annotate(
        total_spent=Sum('user__order__total_amount',
                       filter=Q(user__order__status='delivered'))
    ).aggregate(avg=Avg('total_spent'))['avg'] or 0
    
    # Customer retention
    returning_customers = Profile.objects.filter(
        user__order__created_at__date__range=[start_date, end_date]
    ).distinct().count()
    
    return {
        'high_value_customers': high_value_customers,
        'medium_value_customers': medium_value_customers,
        'low_value_customers': low_value_customers,
        'avg_clv': float(avg_clv),
        'returning_customers': returning_customers,
    }


def get_product_analytics(start_date, end_date):
    """Get detailed product analytics"""
    # Top selling products
    top_products = Product.objects.annotate(
        units_sold=Sum('orderitem__quantity',
                      filter=Q(orderitem__order__status='delivered',
                              orderitem__order__created_at__date__range=[start_date, end_date]))
    ).order_by('-units_sold')[:10]
    
    # Product performance by category
    category_performance = Category.objects.annotate(
        units_sold=Sum('products__orderitem__quantity',
                      filter=Q(products__orderitem__order__status='delivered',
                              products__orderitem__order__created_at__date__range=[start_date, end_date])),
        revenue=Sum('products__orderitem__order__total_amount',
                   filter=Q(products__orderitem__order__status='delivered',
                           products__orderitem__order__created_at__date__range=[start_date, end_date]))
    ).order_by('-revenue')
    
    # Inventory metrics
    low_stock_products = Product.objects.filter(
        stock_quantity__lt=F('reorder_threshold')
    ).count()
    
    out_of_stock_products = Product.objects.filter(
        stock_quantity=0
    ).count()
    
    return {
        'top_products': top_products,
        'category_performance': category_performance,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
    }


def get_marketing_analytics(start_date, end_date):
    """Get marketing analytics data"""
    # This would typically integrate with marketing platforms
    # For now, we'll provide placeholder data
    return {
        'email_campaigns': 0,
        'social_media_posts': 0,
        'marketing_spend': 0,
        'marketing_revenue': 0,
        'roi': 0,
    }


def get_ai_performance_analytics(start_date, end_date):
    """Get AI/ML performance analytics"""
    # Recommendation performance
    total_recommendations = 1000  # Placeholder
    recommendations_clicked = 150  # Placeholder
    recommendations_converted = 25  # Placeholder
    
    click_rate = (recommendations_clicked / total_recommendations * 100) if total_recommendations > 0 else 0
    conversion_rate = (recommendations_converted / recommendations_clicked * 100) if recommendations_clicked > 0 else 0
    
    return {
        'total_recommendations': total_recommendations,
        'recommendations_clicked': recommendations_clicked,
        'recommendations_converted': recommendations_converted,
        'click_rate': click_rate,
        'conversion_rate': conversion_rate,
    }


# Chart data functions for API

def get_revenue_chart_data(start_date, end_date):
    """Get revenue chart data for API"""
    data = []
    current_date = start_date
    while current_date <= end_date:
        daily_revenue = Order.objects.filter(
            created_at__date=current_date,
            status='delivered'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'revenue': float(daily_revenue)
        })
        current_date += timedelta(days=1)
    
    return {'data': data}


def get_orders_chart_data(start_date, end_date):
    """Get orders chart data for API"""
    data = []
    current_date = start_date
    while current_date <= end_date:
        daily_orders = Order.objects.filter(
            created_at__date=current_date
        ).count()
        
        data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'orders': daily_orders
        })
        current_date += timedelta(days=1)
    
    return {'data': data}


def get_customers_chart_data(start_date, end_date):
    """Get customers chart data for API"""
    data = []
    current_date = start_date
    while current_date <= end_date:
        new_customers = Profile.objects.filter(
            created_at__date=current_date
        ).count()
        
        data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'customers': new_customers
        })
        current_date += timedelta(days=1)
    
    return {'data': data}


def get_products_chart_data(start_date, end_date):
    """Get products chart data for API"""
    data = []
    current_date = start_date
    while current_date <= end_date:
        products_sold = OrderItem.objects.filter(
            order__created_at__date=current_date,
            order__status='delivered'
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'products_sold': products_sold
        })
        current_date += timedelta(days=1)
    
    return {'data': data}


def get_ai_chart_data(start_date, end_date):
    """Get AI performance chart data for API"""
    data = []
    current_date = start_date
    while current_date <= end_date:
        # Placeholder data - would integrate with actual AI metrics
        data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'recommendations': 100,
            'clicks': 15,
            'conversions': 3
        })
        current_date += timedelta(days=1)
    
    return {'data': data}
