from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem, OrderFeedback, AssociationRule, RecommendationLog, SearchQuery

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['added_at']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    inlines = [CartItemInline]
    list_display = ['buyer', 'total_items', 'total_price', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
    search_fields = ['buyer__user__username']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['price_at_purchase']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    list_display = ['order_number', 'user', 'status', 'payment_status', 'total_amount', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'user__username', 'shipping_name']
    readonly_fields = ['order_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'order_number', 'user', 'profile')
        }),
        ('Status', {
            'fields': ('status', 'payment_status')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'tax_amount', 'shipping_cost', 'discount_amount', 'total_amount')
        }),
        ('Shipping Information', {
            'fields': ('shipping_name', 'shipping_address', 'shipping_city', 'shipping_state', 'shipping_zip', 'shipping_country', 'shipping_phone')
        }),
        ('Delivery Preferences', {
            'fields': ('preferred_date', 'preferred_time', 'delivery_method', 'special_instructions')
        }),
        ('Feedback', {
            'fields': ('feedback_given',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price_at_purchase', 'total_price']
    list_filter = ['order__status']
    search_fields = ['order__order_number', 'product__name']

@admin.register(OrderFeedback)
class OrderFeedbackAdmin(admin.ModelAdmin):
    list_display = ['order', 'user', 'overall_rating', 'created_at']
    list_filter = ['overall_rating', 'created_at']
    search_fields = ['order__order_number', 'user__username']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(AssociationRule)
class AssociationRuleAdmin(admin.ModelAdmin):
    list_display = ['consequent_product', 'confidence', 'support', 'lift', 'is_active']
    list_filter = ['is_active', 'confidence']
    search_fields = ['consequent_product__name']
    readonly_fields = ['antecedent_products']

@admin.register(RecommendationLog)
class RecommendationLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'recommendation_type', 'clicked', 'created_at']
    list_filter = ['recommendation_type', 'clicked', 'created_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at']

@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ['query', 'user', 'results_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['query', 'user__username']
    readonly_fields = ['created_at']