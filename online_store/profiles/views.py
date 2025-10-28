from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Profile, Wishlist
from checkout.models import Order, OrderItem, CustomerNotification
from item.models import Product
from .decorators import customer_required

@login_required
@customer_required
def profile(request):
    """Display user profile with order history and wishlist"""
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)
    
    # Get recent orders (last 5)
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Get wishlist items
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')[:5]
    
    context = {
        'profile': profile,
        'recent_orders': recent_orders,
        'wishlist_items': wishlist_items,
    }
    
    return render(request, 'profiles/profile.html', context)

@login_required
@customer_required
def edit_profile(request):
    """Edit user profile"""
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)
    
    if request.method == 'POST':
        profile.first_name = request.POST.get('first_name', profile.first_name)
        profile.last_name = request.POST.get('last_name', profile.last_name)
        profile.biography = request.POST.get('biography', profile.biography)
        profile.address = request.POST.get('address', profile.address)
        profile.save()
        return redirect('profiles:profile')
    
    return render(request, 'profiles/edit_profile.html', {'profile': profile})

@login_required
@customer_required
def demographics_form(request):
    """Collect demographics for AI prediction"""
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)
    
    if request.method == 'POST':
        profile.age = request.POST.get('age')
        profile.gender = request.POST.get('gender')
        profile.occupation = request.POST.get('occupation')
        profile.education = request.POST.get('education')
        profile.income_range = request.POST.get('income_range')
        profile.save()
        return redirect('profiles:profile')
    
    return render(request, 'profiles/demographics_form.html', {'profile': profile})

@login_required
@customer_required
def order_history(request):
    """View complete order history"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(orders, 10)
    page = request.GET.get('page')
    orders_page = paginator.get_page(page)
    
    context = {
        'orders': orders_page,
    }
    
    return render(request, 'profiles/order_history.html', context)

@login_required
def wishlist(request):
    """View user's wishlist"""
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    
    # Pagination
    paginator = Paginator(wishlist_items, 12)
    page = request.GET.get('page')
    wishlist_page = paginator.get_page(page)
    
    context = {
        'wishlist_items': wishlist_page,
    }
    
    return render(request, 'profiles/wishlist.html', context)

@login_required
@require_POST
def toggle_wishlist(request, product_id):
    """Add or remove product from wishlist"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if not created:
        wishlist_item.delete()
        return JsonResponse({'status': 'removed', 'message': 'Removed from wishlist'})
    else:
        return JsonResponse({'status': 'added', 'message': 'Added to wishlist'})

@login_required
def order_tracking(request, order_id):
    """View detailed order tracking information"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    # Check if there's a return request
    return_request = None
    try:
        return_request = order.return_request
    except:
        pass
    
    # Order status timeline
    status_timeline = [
        {
            'status': 'pending',
            'title': 'Order Placed',
            'description': 'Your order has been received and is being processed.',
            'completed': order.status in ['confirmed', 'processing', 'shipped', 'delivered'],
            'date': order.created_at
        },
        {
            'status': 'confirmed',
            'title': 'Order Confirmed',
            'description': 'Your order has been confirmed and payment processed.',
            'completed': order.status in ['processing', 'shipped', 'delivered'],
            'date': order.created_at if order.status != 'pending' else None
        },
        {
            'status': 'processing',
            'title': 'Processing',
            'description': 'Your order is being prepared for shipment.',
            'completed': order.status in ['shipped', 'delivered'],
            'date': order.updated_at if order.status in ['shipped', 'delivered'] else None
        },
        {
            'status': 'shipped',
            'title': 'Shipped',
            'description': 'Your order has been shipped and is on its way.',
            'completed': order.status == 'delivered',
            'date': order.updated_at if order.status == 'delivered' else None
        },
        {
            'status': 'delivered',
            'title': 'Delivered',
            'description': 'Your order has been delivered successfully.',
            'completed': order.status == 'delivered',
            'date': order.completed_at if order.completed_at else order.updated_at
        }
    ]
    
    context = {
        'order': order,
        'status_timeline': status_timeline,
        'return_request': return_request,
    }
    
    return render(request, 'profiles/order_tracking.html', context)

@login_required
@require_POST
def cancel_order(request, order_id):
    """Cancel a pending order with automatic refund processing"""
    from django.db import transaction
    from checkout.models import CustomerNotification
    from admin_panel.models import AuditLog
    
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    if not order.can_be_cancelled:
        messages.error(request, 'This order cannot be cancelled.')
        return redirect('profiles:order_tracking', order_id=order.order_id)
    
    try:
        with transaction.atomic():
            # Update order status
            order.status = 'cancelled'
            order.payment_status = 'refunded'  # Automatic refund
            order.save()
            
            # Restore product stock
            for order_item in order.order_items.all():
                order_item.product.stock_quantity += order_item.quantity
                order_item.product.save()
            
            # Log the cancellation
            AuditLog.objects.create(
                user=request.user,
                action='ORDER_CANCELLED',
                description=f'Order #{order.order_number} cancelled by customer',
                new_values={
                    'order_id': order.order_id,
                    'order_number': order.order_number,
                    'refund_amount': float(order.total_amount),
                    'items_restored': order.order_items.count(),
                }
            )
            
            # Send notification to customer
            CustomerNotification.create_notification(
                user=order.user,
                notification_type='order_cancelled',
                title='Order Cancelled',
                message=f'Your order #{order.order_number} has been cancelled successfully. A refund of ${order.total_amount} will be processed and appear in your account within 3-5 business days.',
                order=order
            )
            
            messages.success(request, f'Order {order.order_number} has been cancelled successfully. Your refund of ${order.total_amount} will be processed within 3-5 business days.')
            
    except Exception as e:
        messages.error(request, f'Error cancelling order: {str(e)}')
    
    return redirect('profiles:order_tracking', order_id=order.order_id)

@login_required
@require_POST
def return_order(request, order_id):
    """Initiate return for a delivered order within 2 weeks"""
    from checkout.models import OrderReturn
    from checkout.models import CustomerNotification
    from admin_panel.models import AuditLog
    
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    # Check if order can be returned (delivered within 2 weeks)
    if not order.can_be_returned:
        messages.error(request, 'This order cannot be returned. Returns are only allowed within 2 weeks of delivery.')
        return redirect('profiles:order_tracking', order_id=order.order_id)
    
    # Check if return request already exists
    if order.has_return_request:
        messages.error(request, 'A return request already exists for this order.')
        return redirect('profiles:order_tracking', order_id=order.order_id)
    
    try:
        # Create return request
        return_request = OrderReturn.objects.create(
            order=order,
            reason=request.POST.get('reason', ''),
            description=request.POST.get('description', ''),
            status='pending'
        )
        
        # Log the return request
        AuditLog.objects.create(
            user=request.user,
            action='RETURN_REQUESTED',
            description=f'Return requested for Order #{order.order_number}',
            new_values={
                'return_id': return_request.id,
                'order_id': order.order_id,
                'reason': return_request.reason,
                'description': return_request.description,
            }
        )
        
        # Send notification to customer
        CustomerNotification.create_notification(
            user=order.user,
            notification_type='return_requested',
            title='Return Request Submitted',
            message=f'Your return request for Order #{order.order_number} has been submitted and is under review. You will be notified once it\'s approved.',
            order=order,
            return_request=return_request
        )
        
        messages.success(request, f'Return request submitted for order {order.order_number}. We will review your request and notify you of the approval status.')
        
    except Exception as e:
        messages.error(request, f'Error submitting return request: {str(e)}')
    
    return redirect('profiles:order_tracking', order_id=order.order_id)

@login_required
def notifications(request):
    """View user notifications"""
    notifications = CustomerNotification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark all notifications as read when viewing
    notifications.update(is_read=True)
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page = request.GET.get('page')
    notifications_page = paginator.get_page(page)
    
    context = {
        'notifications': notifications_page,
    }
    
    return render(request, 'profiles/notifications.html', context)

@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(CustomerNotification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    return JsonResponse({'success': True})

@login_required
def reorder(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    from checkout.models import Cart, CartItem
    try:
        cart = Cart.objects.get(buyer=request.user.profile)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(buyer=request.user.profile)
    
    # Add items from order to cart
    added_items = 0
    for order_item in order.order_items.all():
        if order_item.product.is_in_stock:
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=order_item.product,
                defaults={'quantity': order_item.quantity}
            )
            if not created:
                cart_item.quantity += order_item.quantity
                cart_item.save()
            added_items += 1
    
    if added_items > 0:
        messages.success(request, f'Added {added_items} item(s) to your cart!')
        return redirect('checkout:checkout')
    else:
        messages.warning(request, 'No items from this order are currently in stock.')
        return redirect('profiles:order_history')