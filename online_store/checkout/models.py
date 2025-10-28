from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models import Sum, F, Case, When, DecimalField
from profiles.models import Profile
from item.models import Product
import uuid

class Cart(models.Model):
    """Shopping cart for users - enhanced from your original"""
    buyer = models.OneToOneField(Profile, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.buyer.user.username}'s cart"
    
    @property
    def total_items(self):
        """Calculate total number of items in cart - optimized"""
        return self.cart_items.aggregate(total=Sum('quantity'))['total'] or 0
    
    @property
    def subtotal(self):
        """Calculate subtotal (before tax and shipping)"""
        return self.cart_items.aggregate(
            total=Sum(
                F('quantity') * Case(
                    When(product__discount_price__isnull=False, then=F('product__discount_price')),
                    default=F('product__price'),
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                )
            )
        )['total'] or 0
    
    @property
    def shipping_cost(self):
        """Calculate shipping cost (simplified - free shipping over $50)"""
        if self.subtotal >= 50:
            return 0
        return 10  # $10 flat rate shipping
    
    @property
    def tax_amount(self):
        """Calculate tax amount (simplified - 8% tax)"""
        from decimal import Decimal
        return self.subtotal * Decimal('0.08')
    
    @property
    def discount_amount(self):
        """Calculate total discount from loyalty rewards"""
        return self.discounts.aggregate(total=Sum('discount_amount'))['total'] or 0
    
    @property
    def total_price(self):
        """Calculate total price including tax and shipping, minus discounts"""
        return self.subtotal + self.shipping_cost + self.tax_amount - self.discount_amount

    @property
    def is_empty(self):
        """Check if cart is empty"""
        return self.total_items == 0

class CartItem(models.Model):
    """Items in shopping cart - enhanced from your original"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Changed from Items to Product
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['cart', 'product']  # Prevent duplicate products in cart

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"
    
    @property
    def total_price(self):
        """Calculate total price for this cart item"""
        return self.product.current_price * self.quantity


class CartDiscount(models.Model):
    """Loyalty rewards applied to cart"""
    DISCOUNT_TYPES = [
        ('loyalty_points', 'Loyalty Points'),
        ('loyalty_reward', 'Loyalty Reward'),
        ('promo_code', 'Promo Code'),
    ]
    
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='discounts')
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    points_used = models.PositiveIntegerField(default=0, help_text="Loyalty points used for this discount")
    reward = models.ForeignKey('loyalty.LoyaltyReward', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=200)
    applied_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-applied_at']
    
    def __str__(self):
        return f"{self.cart} - {self.description} (${self.discount_amount})"

class Order(models.Model):
    """Customer orders - enhanced from your PastOrder"""
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    # Order Identification
    order_id = models.AutoField(primary_key=True)
    order_number = models.CharField(max_length=20, unique=True, help_text="Human-readable order number")
    
    # User and Profile
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True)
    
    # Order Status
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Pricing Breakdown (new for e-commerce)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Shipping Information (enhanced from your original)
    shipping_name = models.CharField(max_length=100, blank=True)
    shipping_address = models.TextField(blank=True)
    shipping_city = models.CharField(max_length=100, blank=True)
    shipping_state = models.CharField(max_length=100, blank=True)
    shipping_zip = models.CharField(max_length=10, blank=True)
    shipping_country = models.CharField(max_length=100, default='Singapore')
    shipping_phone = models.CharField(max_length=20, blank=True)
    
    # Delivery Preferences (keeping your original concept)
    preferred_date = models.DateField(null=True, blank=True)
    preferred_time = models.TimeField(null=True, blank=True)
    delivery_method = models.CharField(max_length=55, null=True, blank=True)
    special_instructions = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Feedback tracking (keeping your original)
    feedback_given = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number}"
    
    def save(self, *args, **kwargs):
        """Generate order number if not provided"""
        if not self.order_number:
            # Use a more robust order number generation
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            # Use a random string instead of pk since pk might not exist yet
            import uuid
            random_suffix = str(uuid.uuid4())[:8].upper()
            self.order_number = f"AM{timestamp}{random_suffix}"
        super().save(*args, **kwargs)
    
    @property
    def is_completed(self):
        """Check if order is completed"""
        return self.status == 'delivered'
    
    @property
    def can_be_cancelled(self):
        """Check if order can be cancelled (before shipping)"""
        return self.status in ['pending', 'confirmed', 'processing']
    
    @property
    def can_be_returned(self):
        """Check if order can be returned (delivered within 2 weeks)"""
        if self.status != 'delivered':
            return False
        
        # Check if delivered within last 2 weeks
        from django.utils import timezone
        from datetime import timedelta
        
        if self.completed_at:
            two_weeks_ago = timezone.now() - timedelta(weeks=2)
            return self.completed_at >= two_weeks_ago
        
        return False
    
    @property
    def has_return_request(self):
        """Check if order has an active return request"""
        try:
            return self.return_request.status != 'refunded'
        except:
            return False

class OrderItem(models.Model):
    """Items within an order - enhanced from your PastOrderItem"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Changed from Items to Product
    quantity = models.PositiveIntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price when order was placed")
    
    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"
    
    @property
    def total_price(self):
        """Calculate total price for this order item"""
        return self.price_at_purchase * self.quantity

class OrderReturn(models.Model):
    """Order return requests"""
    RETURN_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('shipped', 'Shipped Back'),
        ('received', 'Received'),
        ('refunded', 'Refunded'),
        ('closed', 'Closed'),
    ]
    
    RETURN_REASON_CHOICES = [
        ('defective', 'Defective Product'),
        ('wrong_item', 'Wrong Item'),
        ('not_as_described', 'Not as Described'),
        ('changed_mind', 'Changed Mind'),
        ('damaged_shipping', 'Damaged in Shipping'),
        ('other', 'Other'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='return_request')
    reason = models.CharField(max_length=50, choices=RETURN_REASON_CHOICES)
    description = models.TextField(blank=True, help_text="Additional details about the return")
    status = models.CharField(max_length=20, choices=RETURN_STATUS_CHOICES, default='pending')
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    # Admin notes
    admin_notes = models.TextField(blank=True, help_text="Internal notes for admin")
    
    class Meta:
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"Return for Order #{self.order.order_number}"
    
    @property
    def can_be_approved(self):
        """Check if return can be approved"""
        return self.status == 'pending'
    
    @property
    def can_be_shipped(self):
        """Check if return can be marked as shipped"""
        return self.status == 'approved'
    
    @property
    def can_be_received(self):
        """Check if return can be marked as received"""
        return self.status == 'shipped'
    
    @property
    def can_be_refunded(self):
        """Check if return can be refunded"""
        return self.status == 'received'
    
    @property
    def can_be_closed(self):
        """Check if return can be closed"""
        return self.status == 'refunded'

class CustomerNotificationManager(models.Manager):
    """Custom manager for CustomerNotification"""
    
    def unread(self):
        """Return unread notifications"""
        return self.filter(is_read=False)
    
    def read(self):
        """Return read notifications"""
        return self.filter(is_read=True)

class CustomerNotification(models.Model):
    """Customer notifications for order updates, returns, etc."""
    NOTIFICATION_TYPE_CHOICES = [
        ('order_update', 'Order Update'),
        ('order_cancelled', 'Order Cancelled'),
        ('order_shipped', 'Order Shipped'),
        ('order_delivered', 'Order Delivered'),
        ('return_requested', 'Return Requested'),
        ('return_approved', 'Return Approved'),
        ('return_rejected', 'Return Rejected'),
        ('return_shipped', 'Return Shipped'),
        ('return_received', 'Return Received'),
        ('refund_processed', 'Refund Processed'),
        ('return_closed', 'Return Closed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional related objects
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    return_request = models.ForeignKey(OrderReturn, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    # Custom managers
    objects = CustomerNotificationManager()
    unread = CustomerNotificationManager()
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    @classmethod
    def create_notification(cls, user, notification_type, title, message, order=None, return_request=None):
        """Create a new notification"""
        return cls.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            order=order,
            return_request=return_request
        )

class OrderFeedback(models.Model):
    """Order feedback - enhanced from your Feedback model"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='feedbacks')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    
    # Overall order rating
    overall_rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    # Detailed ratings
    product_quality_rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    delivery_rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    packaging_rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    
    # Feedback content
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['order', 'user']  # One feedback per user per order

    def __str__(self):
        return f"Feedback for Order #{self.order.order_number} by {self.user.username}"

# AI/ML Integration Models for AuroraMart

class AssociationRule(models.Model):
    """Association rules for product recommendations"""
    antecedent_products = models.JSONField(help_text="List of product IDs that trigger recommendation")
    consequent_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='recommended_by')
    confidence = models.DecimalField(max_digits=5, decimal_places=4)
    support = models.DecimalField(max_digits=5, decimal_places=4)
    lift = models.DecimalField(max_digits=5, decimal_places=4)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"If {self.antecedent_products} then {self.consequent_product.name} (conf: {self.confidence})"

class RecommendationLog(models.Model):
    """Track AI recommendations shown to users"""
    RECOMMENDATION_TYPE_CHOICES = [
        ('onboarding', 'Onboarding Prediction'),
        ('cart', 'Cart Recommendation'),
        ('product_page', 'Product Page Recommendation'),
        ('category', 'Category Recommendation'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPE_CHOICES)
    recommended_products = models.JSONField(help_text="List of product IDs recommended")
    context_data = models.JSONField(default=dict, help_text="Additional context (cart items, etc.)")
    clicked = models.BooleanField(default=False)
    clicked_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.recommendation_type} - {self.created_at}"

class SearchQuery(models.Model):
    """Track search queries for analytics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='searches', null=True, blank=True)
    query = models.CharField(max_length=200)
    results_count = models.PositiveIntegerField()
    clicked_results = models.JSONField(default=list, help_text="Product IDs that were clicked")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"'{self.query}' - {self.results_count} results"