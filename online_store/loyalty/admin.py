from django.contrib import admin
from .models import (
    LoyaltyTier, LoyaltyAccount, LoyaltyTransaction,
    LoyaltyReward, LoyaltyRedemption, LoyaltyNotification,
    LoyaltyAnalytics
)


@admin.register(LoyaltyTier)
class LoyaltyTierAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'min_points', 'point_multiplier', 'discount_percentage', 'is_active']
    list_filter = ['is_active', 'free_shipping', 'priority_support', 'exclusive_access']
    search_fields = ['display_name', 'name']
    ordering = ['min_points']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'display_name', 'description', 'is_active')
        }),
        ('Tier Requirements', {
            'fields': ('min_points', 'max_points')
        }),
        ('Benefits', {
            'fields': ('point_multiplier', 'discount_percentage', 'free_shipping', 'priority_support', 'exclusive_access')
        }),
        ('Display', {
            'fields': ('color', 'icon')
        }),
    )


@admin.register(LoyaltyAccount)
class LoyaltyAccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_tier', 'points_balance', 'lifetime_points', 'is_active', 'last_activity']
    list_filter = ['current_tier', 'is_active', 'join_date']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['join_date', 'last_activity']
    
    fieldsets = (
        ('Account Information', {
            'fields': ('user', 'is_active')
        }),
        ('Points', {
            'fields': ('points_balance', 'lifetime_points', 'current_tier')
        }),
        ('Timestamps', {
            'fields': ('join_date', 'last_activity'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    list_display = ['account', 'points', 'transaction_type', 'source', 'created_at']
    list_filter = ['transaction_type', 'source', 'created_at']
    search_fields = ['account__user__username', 'description']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('account', 'points', 'transaction_type', 'source', 'description')
        }),
        ('Related Order', {
            'fields': ('order',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LoyaltyReward)
class LoyaltyRewardAdmin(admin.ModelAdmin):
    list_display = ['name', 'reward_type', 'points_cost', 'is_active', 'current_redemptions', 'valid_until']
    list_filter = ['reward_type', 'is_active', 'valid_from', 'valid_until']
    search_fields = ['name', 'description']
    date_hierarchy = 'valid_from'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'reward_type', 'is_active')
        }),
        ('Cost & Limits', {
            'fields': ('points_cost', 'max_redemptions', 'current_redemptions')
        }),
        ('Reward Details', {
            'fields': ('discount_percentage', 'discount_amount', 'free_product')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until')
        }),
    )


@admin.register(LoyaltyRedemption)
class LoyaltyRedemptionAdmin(admin.ModelAdmin):
    list_display = ['account', 'reward', 'points_used', 'status', 'redeemed_at', 'expires_at']
    list_filter = ['status', 'redeemed_at', 'expires_at']
    search_fields = ['account__user__username', 'reward__name']
    readonly_fields = ['id', 'redeemed_at']
    date_hierarchy = 'redeemed_at'
    
    fieldsets = (
        ('Redemption Details', {
            'fields': ('account', 'reward', 'points_used', 'status')
        }),
        ('Related Order', {
            'fields': ('order',)
        }),
        ('Timestamps', {
            'fields': ('redeemed_at', 'expires_at', 'used_at')
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )


@admin.register(LoyaltyNotification)
class LoyaltyNotificationAdmin(admin.ModelAdmin):
    list_display = ['account', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['account__user__username', 'title', 'message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('account', 'notification_type', 'title', 'message', 'is_read')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(LoyaltyAnalytics)
class LoyaltyAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_accounts', 'active_accounts', 'total_points_earned', 'total_points_redeemed']
    list_filter = ['date']
    search_fields = ['date']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Date', {
            'fields': ('date',)
        }),
        ('Account Metrics', {
            'fields': ('total_accounts', 'active_accounts')
        }),
        ('Points Metrics', {
            'fields': ('total_points_earned', 'total_points_redeemed', 'total_redemptions')
        }),
        ('Tier Distribution', {
            'fields': ('tier_distribution',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
