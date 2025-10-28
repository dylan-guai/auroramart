from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import transaction
import logging
import uuid

from .models import Cart, CartItem, Order, OrderItem, CartDiscount
from item.models import Product
from core.ml_service import ml_service
from loyalty.models import LoyaltyAccount, LoyaltyReward
from .decorators import customer_required

logger = logging.getLogger(__name__)

@login_required
@customer_required
def cart_view(request):
    """Display shopping cart with AI-powered recommendations"""
    try:
        cart = Cart.objects.get(buyer=request.user.profile)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(buyer=request.user.profile)
    
    # AI-Powered Cart Recommendations
    recommended_products = []
    if cart.cart_items.exists():
        try:
            # Get SKUs of items in cart
            cart_skus = list(cart.cart_items.values_list('product__sku', flat=True))
            
            # Get AI recommendations based on cart contents
            recommended_skus = ml_service.get_product_recommendations(
                cart_skus, 
                metric='confidence', 
                top_n=5
            )
            
            if recommended_skus:
                # Get product objects for recommended SKUs
                recommended_products = Product.objects.filter(
                    sku__in=recommended_skus,
                    is_active=True,
                    stock_quantity__gt=0
                ).exclude(
                    id__in=cart.cart_items.values_list('product_id', flat=True)
                ).select_related('category', 'brand')[:5]
                
        except Exception as e:
            logger.error(f"Cart recommendation error: {e}")
            recommended_products = []
    
    # Get loyalty information
    loyalty_account = None
    available_rewards = []
    try:
        loyalty_account = request.user.loyalty_account
        available_rewards = LoyaltyReward.objects.filter(
            is_active=True,
            valid_from__lte=timezone.now(),
            valid_until__gte=timezone.now()
        ).order_by('points_cost')
    except LoyaltyAccount.DoesNotExist:
        pass
    
    return render(request, 'checkout/cart.html', {
        'cart': cart,
        'recommended_products': recommended_products,
        'loyalty_account': loyalty_account,
        'available_rewards': available_rewards
    })

@login_required
def checkout(request):
    """Checkout process with AI-powered upsell recommendations"""
    try:
        cart = Cart.objects.get(buyer=request.user.profile)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(buyer=request.user.profile)
    
    # AI-Powered Upsell Recommendations
    upsell_products = []
    if cart.cart_items.exists():
        try:
            # Get SKUs of items in cart
            cart_skus = list(cart.cart_items.values_list('product__sku', flat=True))
            
            # Get AI recommendations for upsell
            recommended_skus = ml_service.get_product_recommendations(
                cart_skus, 
                metric='lift',  # Use lift for upsell recommendations
                top_n=3
            )
            
            if recommended_skus:
                # Get product objects for recommended SKUs
                upsell_products = Product.objects.filter(
                    sku__in=recommended_skus,
                    is_active=True,
                    stock_quantity__gt=0
                ).exclude(
                    id__in=cart.cart_items.values_list('product_id', flat=True)
                ).select_related('category', 'brand')[:3]
                
        except Exception as e:
            logger.error(f"Upsell recommendation error: {e}")
            upsell_products = []
    
    if request.method == 'POST':
        # Validate cart has items
        if not cart.cart_items.exists():
            messages.error(request, 'Your cart is empty.')
            return redirect('checkout:cart_view')
        
        # Get form data
        shipping_name = request.POST.get('shipping_name', '').strip()
        shipping_address = request.POST.get('shipping_address', '').strip()
        shipping_city = request.POST.get('shipping_city', '').strip()
        shipping_state = request.POST.get('shipping_state', '').strip()
        shipping_zip = request.POST.get('shipping_zip', '').strip()
        shipping_country = request.POST.get('shipping_country', '').strip()
        shipping_phone = request.POST.get('shipping_phone', '').strip()
        payment_method = request.POST.get('payment_method', '').strip()
        
        # Validate required fields
        if not all([shipping_name, shipping_address, shipping_city, shipping_state, shipping_zip, shipping_country, payment_method]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'checkout/checkout.html', {
                'cart': cart,
                'upsell_products': upsell_products
            })
        
        # Process payment (simplified for demo - in production, integrate with real payment gateway)
        if payment_method == 'credit_card':
            # Simulate payment processing
            payment_status = 'completed'  # In real implementation, this would be determined by payment gateway
        elif payment_method == 'paypal':
            payment_status = 'completed'  # In real implementation, this would be determined by PayPal API
        else:
            messages.error(request, 'Invalid payment method selected.')
            return render(request, 'checkout/checkout.html', {
                'cart': cart,
                'upsell_products': upsell_products
            })
        
        # Create order
        try:
            with transaction.atomic():
                # Generate unique order number
                order_number = f"ORD-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
                
                # Create order
                order = Order.objects.create(
                    user=request.user,
                    profile=request.user.profile,
                    order_number=order_number,
                    shipping_name=shipping_name,
                    shipping_address=shipping_address,
                    shipping_city=shipping_city,
                    shipping_state=shipping_state,
                    shipping_zip=shipping_zip,
                    shipping_country=shipping_country,
                    shipping_phone=shipping_phone,
                    subtotal=cart.subtotal,
                    shipping_cost=cart.shipping_cost,
                    tax_amount=cart.tax_amount,
                    total_amount=cart.total_price,
                    payment_status=payment_status,
                    status='pending'
                )
                
                # Create order items
                for cart_item in cart.cart_items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price_at_purchase=cart_item.product.price
                    )
                    
                    # Update product stock
                    cart_item.product.stock_quantity -= cart_item.quantity
                    cart_item.product.save()
                
                # Clear cart
                cart.cart_items.all().delete()
                
                messages.success(request, f'Order placed successfully! Order number: {order_number}')
                return redirect('checkout:checkout_success', order_id=order.order_id)
                
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            messages.error(request, 'There was an error processing your order. Please try again.')
            return render(request, 'checkout/checkout.html', {
                'cart': cart,
                'upsell_products': upsell_products
            })
    
    return render(request, 'checkout/checkout.html', {
        'cart': cart,
        'upsell_products': upsell_products
    })

@login_required
def checkout_success(request, order_id):
    """Checkout success page"""
    try:
        order = Order.objects.get(order_id=order_id, user=request.user)
        return render(request, 'checkout/success.html', {'order': order})
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('index')

@login_required
@require_POST
def update_cart_item(request, item_id):
    """Update cart item quantity via AJAX with comprehensive error handling"""
    try:
        cart_item = CartItem.objects.get(
            id=item_id,
            cart__buyer=request.user.profile
        )
    except CartItem.DoesNotExist:
        logger.warning(f"Cart item {item_id} not found for user {request.user.username}")
        return JsonResponse({
            'success': False,
            'message': 'Item not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error retrieving cart item {item_id} for user {request.user.username}: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error accessing cart item'
        }, status=500)
    
    # Validate quantity input
    try:
        new_quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid quantity provided by user {request.user.username}: {request.POST.get('quantity')}")
        return JsonResponse({
            'success': False,
            'message': 'Invalid quantity specified'
        }, status=400)
    
    # Validate quantity bounds
    if new_quantity < 0:
        logger.warning(f"Negative quantity provided by user {request.user.username}: {new_quantity}")
        return JsonResponse({
            'success': False,
            'message': 'Quantity cannot be negative'
        }, status=400)
    
    if new_quantity > 99:
        logger.warning(f"Excessive quantity requested by user {request.user.username}: {new_quantity}")
        return JsonResponse({
            'success': False,
            'message': 'Maximum quantity per item is 99'
        }, status=400)
    
    # Check stock availability
    if new_quantity > cart_item.product.stock_quantity:
        logger.info(f"Stock limit exceeded for product {cart_item.product.id} by user {request.user.username}")
        return JsonResponse({
            'success': False,
            'message': f'Only {cart_item.product.stock_quantity} items available in stock'
        }, status=400)
    
    try:
        if new_quantity < 1:
            cart_item.delete()
            logger.info(f"Cart item {item_id} removed by user {request.user.username}")
            return JsonResponse({
                'success': True,
                'removed': True,
                'message': 'Item removed from cart'
            })
        
        cart_item.quantity = new_quantity
        cart_item.save()
        
        # Get updated cart totals
        cart = cart_item.cart
        
        logger.info(f"Cart item {item_id} updated by user {request.user.username}, new quantity: {new_quantity}")
        
        return JsonResponse({
            'success': True,
            'removed': False,
            'item_id': cart_item.id,
            'quantity': cart_item.quantity,
            'item_total': float(cart_item.total_price),
            'cart_total': float(cart.total_price),
            'cart_items': cart.total_items,
            'message': 'Quantity updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating cart item {item_id} for user {request.user.username}: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error updating item'
        }, status=500)

@login_required
@require_POST
def remove_cart_item(request, item_id):
    """Remove cart item via AJAX"""
    try:
        cart_item = CartItem.objects.get(
            id=item_id,
            cart__buyer=request.user.profile
        )
        
        cart = cart_item.cart
        cart_item.delete()
        
        return JsonResponse({
            'success': True,
            'cart_total': float(cart.total_price),
            'cart_items': cart.total_items,
            'message': 'Item removed from cart'
        })
        
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Item not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error removing cart item: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error removing item'
        }, status=500)


@login_required
@require_POST
def apply_loyalty_points(request):
    """Apply loyalty points as discount to cart"""
    try:
        cart = Cart.objects.get(buyer=request.user.profile)
    except Cart.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Cart not found'
        }, status=404)
    
    try:
        loyalty_account = request.user.loyalty_account
    except LoyaltyAccount.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Loyalty account not found'
        }, status=404)
    
    try:
        points_to_redeem = int(request.POST.get('points', 0))
    except (ValueError, TypeError):
        return JsonResponse({
            'success': False,
            'message': 'Invalid points amount'
        }, status=400)
    
    # Validate points
    if points_to_redeem <= 0:
        return JsonResponse({
            'success': False,
            'message': 'Points must be greater than 0'
        }, status=400)
    
    if points_to_redeem > loyalty_account.points_balance:
        return JsonResponse({
            'success': False,
            'message': f'Insufficient points. You have {loyalty_account.points_balance} points available'
        }, status=400)
    
    # Calculate discount (100 points = $1)
    discount_amount = points_to_redeem / 100
    
    # Check if discount exceeds cart subtotal
    if discount_amount > cart.subtotal:
        discount_amount = cart.subtotal
        points_to_redeem = int(discount_amount * 100)
    
    try:
        with transaction.atomic():
            # Remove any existing loyalty point discounts
            cart.discounts.filter(discount_type='loyalty_points').delete()
            
            # Create new discount
            CartDiscount.objects.create(
                cart=cart,
                discount_type='loyalty_points',
                discount_amount=discount_amount,
                points_used=points_to_redeem,
                description=f'Loyalty Points Discount ({points_to_redeem} points)'
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Applied {points_to_redeem} points for ${discount_amount:.2f} discount',
                'discount_amount': float(discount_amount),
                'points_used': points_to_redeem,
                'new_total': float(cart.total_price)
            })
            
    except Exception as e:
        logger.error(f"Error applying loyalty points: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error applying loyalty points'
        }, status=500)


@login_required
@require_POST
def apply_loyalty_reward(request, reward_id):
    """Apply a specific loyalty reward to cart"""
    try:
        cart = Cart.objects.get(buyer=request.user.profile)
    except Cart.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Cart not found'
        }, status=404)
    
    try:
        loyalty_account = request.user.loyalty_account
    except LoyaltyAccount.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Loyalty account not found'
        }, status=404)
    
    try:
        reward = LoyaltyReward.objects.get(
            id=reward_id,
            is_active=True,
            valid_from__lte=timezone.now(),
            valid_until__gte=timezone.now()
        )
    except LoyaltyReward.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Reward not found or expired'
        }, status=404)
    
    # Check if user has enough points
    if loyalty_account.points_balance < reward.points_cost:
        return JsonResponse({
            'success': False,
            'message': f'Insufficient points. You need {reward.points_cost} points for this reward'
        }, status=400)
    
    # Check if reward is available
    if not reward.is_available:
        return JsonResponse({
            'success': False,
            'message': 'This reward is no longer available'
        }, status=400)
    
    try:
        with transaction.atomic():
            # Remove any existing loyalty reward discounts
            cart.discounts.filter(discount_type='loyalty_reward').delete()
            
            # Calculate discount amount
            discount_amount = 0
            if reward.discount_percentage:
                discount_amount = cart.subtotal * (reward.discount_percentage / 100)
            elif reward.discount_amount:
                discount_amount = reward.discount_amount
            
            # Cap discount at cart subtotal
            if discount_amount > cart.subtotal:
                discount_amount = cart.subtotal
            
            # Create discount
            CartDiscount.objects.create(
                cart=cart,
                discount_type='loyalty_reward',
                discount_amount=discount_amount,
                points_used=reward.points_cost,
                reward=reward,
                description=f'{reward.name} ({reward.points_cost} points)'
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Applied {reward.name} for ${discount_amount:.2f} discount',
                'discount_amount': float(discount_amount),
                'points_used': reward.points_cost,
                'new_total': float(cart.total_price)
            })
            
    except Exception as e:
        logger.error(f"Error applying loyalty reward: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error applying loyalty reward'
        }, status=500)


@login_required
@require_POST
def remove_loyalty_discount(request):
    """Remove loyalty discount from cart"""
    try:
        cart = Cart.objects.get(buyer=request.user.profile)
    except Cart.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Cart not found'
        }, status=404)
    
    try:
        # Remove all loyalty discounts
        cart.discounts.all().delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Loyalty discount removed',
            'new_total': float(cart.total_price)
        })
        
    except Exception as e:
        logger.error(f"Error removing loyalty discount: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error removing loyalty discount'
        }, status=500)