from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count, Sum

from admin_panel.decorators import admin_required, role_required
from checkout.models import Order, OrderItem, CustomerNotification
from admin_panel.models import AuditLog

@admin_required
@role_required(['Admin', 'CRM', 'Inventory'])
def order_management(request):
    """Admin view for managing all orders"""
    orders = Order.objects.select_related('user', 'profile').prefetch_related('order_items__product').order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Filter by payment status
    payment_filter = request.GET.get('payment_status', '')
    if payment_filter:
        orders = orders.filter(payment_status=payment_filter)
    
    # Search by order number or customer
    search_query = request.GET.get('search', '')
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(shipping_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    processing_orders = Order.objects.filter(status='processing').count()
    shipped_orders = Order.objects.filter(status='shipped').count()
    delivered_orders = Order.objects.filter(status='delivered').count()
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'payment_filter': payment_filter,
        'search_query': search_query,
        'status_choices': Order.ORDER_STATUS_CHOICES,
        'payment_status_choices': Order.PAYMENT_STATUS_CHOICES,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
    }
    
    return render(request, 'admin_panel/order_management.html', context)

@admin_required
@role_required(['Admin', 'CRM', 'Inventory'])
def order_detail(request, order_id):
    """Admin view for detailed order information"""
    order = get_object_or_404(Order, order_id=order_id)
    
    # Get order items
    order_items = order.order_items.select_related('product').all()
    
    # Get order history (audit logs)
    order_logs = AuditLog.objects.filter(
        new_values__order_id=order.order_id
    ).order_by('-timestamp')[:10]
    
    # Get return request if exists
    return_request = None
    try:
        return_request = order.return_request
    except:
        pass
    
    context = {
        'order': order,
        'order_items': order_items,
        'order_logs': order_logs,
        'return_request': return_request,
        'status_choices': Order.ORDER_STATUS_CHOICES,
        'payment_status_choices': Order.PAYMENT_STATUS_CHOICES,
    }
    
    return render(request, 'admin_panel/order_detail.html', context)

@admin_required
@role_required(['Admin', 'CRM', 'Inventory'])
@require_POST
def update_order_status(request, order_id):
    """Update order status with proper validation and notifications"""
    order = get_object_or_404(Order, order_id=order_id)
    
    new_status = request.POST.get('status')
    if not new_status or new_status not in [choice[0] for choice in Order.ORDER_STATUS_CHOICES]:
        messages.error(request, 'Invalid status provided.')
        return redirect('admin_panel:order_detail', order_id=order_id)
    
    old_status = order.status
    
    # Validate status transition
    valid_transitions = {
        'pending': ['confirmed', 'cancelled'],
        'confirmed': ['processing', 'cancelled'],
        'processing': ['shipped', 'cancelled'],
        'shipped': ['delivered'],
        'delivered': [],  # Final state
        'cancelled': [],  # Final state
    }
    
    if new_status not in valid_transitions.get(old_status, []):
        messages.error(request, f'Cannot change status from {old_status} to {new_status}.')
        return redirect('admin_panel:order_detail', order_id=order_id)
    
    try:
        with transaction.atomic():
            # Update order status
            order.status = new_status
            order.updated_at = timezone.now()
            
            # Set completion date if delivered
            if new_status == 'delivered' and not order.completed_at:
                order.completed_at = timezone.now()
            
            order.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='ORDER_STATUS_UPDATED',
                description=f'Updated order status from {old_status} to {new_status} for Order #{order.order_number}',
                new_values={
                    'order_id': order.order_id,
                    'order_number': order.order_number,
                    'old_status': old_status,
                    'new_status': new_status,
                    'updated_at': order.updated_at.isoformat(),
                }
            )
            
            # Send notification to customer
            status_messages = {
                'confirmed': 'Your order has been confirmed and payment processed.',
                'processing': 'Your order is being prepared for shipment.',
                'shipped': 'Your order has been shipped and is on its way.',
                'delivered': 'Your order has been delivered successfully.',
                'cancelled': 'Your order has been cancelled.',
            }
            
            if new_status in status_messages:
                CustomerNotification.create_notification(
                    user=order.user,
                    notification_type='order_status_update',
                    title=f'Order Status Update - {order.get_status_display()}',
                    message=f'Order #{order.order_number}: {status_messages[new_status]}',
                    order=order
                )
            
            messages.success(request, f'Order #{order.order_number} status updated to {order.get_status_display()}.')
            
    except Exception as e:
        messages.error(request, f'Error updating order status: {str(e)}')
    
    return redirect('admin_panel:order_detail', order_id=order_id)

@admin_required
@role_required(['Admin', 'CRM'])
@require_POST
def update_payment_status(request, order_id):
    """Update payment status"""
    order = get_object_or_404(Order, order_id=order_id)
    
    new_payment_status = request.POST.get('payment_status')
    if not new_payment_status or new_payment_status not in [choice[0] for choice in Order.PAYMENT_STATUS_CHOICES]:
        messages.error(request, 'Invalid payment status provided.')
        return redirect('admin_panel:order_detail', order_id=order_id)
    
    old_payment_status = order.payment_status
    
    try:
        with transaction.atomic():
            order.payment_status = new_payment_status
            order.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='PAYMENT_STATUS_UPDATED',
                description=f'Updated payment status from {old_payment_status} to {new_payment_status} for Order #{order.order_number}',
                new_values={
                    'order_id': order.order_id,
                    'order_number': order.order_number,
                    'old_payment_status': old_payment_status,
                    'new_payment_status': new_payment_status,
                }
            )
            
            messages.success(request, f'Payment status updated to {order.get_payment_status_display()}.')
            
    except Exception as e:
        messages.error(request, f'Error updating payment status: {str(e)}')
    
    return redirect('admin_panel:order_detail', order_id=order_id)

@admin_required
@role_required(['Admin', 'CRM'])
def order_analytics(request):
    """Order analytics dashboard"""
    from django.db.models import Avg
    
    # Basic statistics
    total_orders = Order.objects.count()
    total_revenue = Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    avg_order_value = Order.objects.aggregate(avg=Avg('total_amount'))['avg'] or 0
    
    # Status distribution
    status_distribution = Order.objects.values('status').annotate(count=Count('id')).order_by('-count')
    
    # Recent orders (last 30 days)
    from datetime import timedelta
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_orders = Order.objects.filter(created_at__gte=thirty_days_ago)
    
    # Daily order counts for chart
    daily_orders = recent_orders.extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'avg_order_value': avg_order_value,
        'status_distribution': status_distribution,
        'daily_orders': list(daily_orders),
    }
    
    return render(request, 'admin_panel/order_analytics.html', context)
