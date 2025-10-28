from django.contrib import admin
from .models import (
    AnalyticsDashboard, AnalyticsWidget, BusinessMetrics,
    CustomerAnalytics, ProductAnalytics, MarketingAnalytics,
    AIPerformanceMetrics, AnalyticsReport
)


@admin.register(AnalyticsDashboard)
class AnalyticsDashboardAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AnalyticsWidget)
class AnalyticsWidgetAdmin(admin.ModelAdmin):
    list_display = ['name', 'dashboard', 'widget_type', 'chart_type', 'is_active', 'position_x', 'position_y']
    list_filter = ['widget_type', 'chart_type', 'is_active', 'dashboard']
    search_fields = ['name', 'title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('dashboard', 'name', 'title', 'description', 'is_active')
        }),
        ('Widget Configuration', {
            'fields': ('widget_type', 'chart_type', 'data_source')
        }),
        ('Layout', {
            'fields': ('position_x', 'position_y', 'width', 'height')
        }),
        ('Refresh Settings', {
            'fields': ('refresh_interval',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BusinessMetrics)
class BusinessMetricsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_revenue', 'total_orders', 'new_customers', 'conversion_rate']
    list_filter = ['date']
    search_fields = ['date']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Date', {
            'fields': ('date',)
        }),
        ('Revenue Metrics', {
            'fields': ('total_revenue', 'gross_profit', 'net_profit')
        }),
        ('Order Metrics', {
            'fields': ('total_orders', 'completed_orders', 'cancelled_orders', 'average_order_value')
        }),
        ('Customer Metrics', {
            'fields': ('new_customers', 'returning_customers', 'total_customers', 'customer_retention_rate')
        }),
        ('Product Metrics', {
            'fields': ('products_sold', 'unique_products_sold', 'top_selling_category')
        }),
        ('Conversion Metrics', {
            'fields': ('page_views', 'unique_visitors', 'conversion_rate', 'cart_abandonment_rate')
        }),
        ('Loyalty Metrics', {
            'fields': ('loyalty_points_earned', 'loyalty_points_redeemed', 'loyalty_redemptions')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CustomerAnalytics)
class CustomerAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['date', 'high_value_customers', 'medium_value_customers', 'low_value_customers', 'customer_lifetime_value']
    list_filter = ['date']
    search_fields = ['date']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Date', {
            'fields': ('date',)
        }),
        ('Demographics', {
            'fields': ('age_distribution', 'gender_distribution', 'location_distribution')
        }),
        ('Behavior Metrics', {
            'fields': ('average_session_duration', 'pages_per_session', 'bounce_rate')
        }),
        ('Purchase Behavior', {
            'fields': ('purchase_frequency', 'average_purchase_value', 'customer_lifetime_value')
        }),
        ('Segmentation', {
            'fields': ('high_value_customers', 'medium_value_customers', 'low_value_customers')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProductAnalytics)
class ProductAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_products_sold', 'low_stock_products', 'out_of_stock_products', 'average_rating']
    list_filter = ['date']
    search_fields = ['date']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Date', {
            'fields': ('date',)
        }),
        ('Sales Performance', {
            'fields': ('total_products_sold', 'revenue_by_category', 'top_selling_products', 'low_selling_products')
        }),
        ('Inventory Metrics', {
            'fields': ('total_inventory_value', 'low_stock_products', 'out_of_stock_products', 'inventory_turnover_rate')
        }),
        ('Product Performance', {
            'fields': ('average_rating', 'total_reviews', 'products_with_reviews')
        }),
        ('Search Analytics', {
            'fields': ('most_searched_products', 'search_no_results', 'search_conversion_rate')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(MarketingAnalytics)
class MarketingAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['date', 'organic_traffic', 'paid_traffic', 'social_traffic', 'marketing_roi']
    list_filter = ['date']
    search_fields = ['date']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Date', {
            'fields': ('date',)
        }),
        ('Traffic Sources', {
            'fields': ('organic_traffic', 'paid_traffic', 'social_traffic', 'direct_traffic', 'referral_traffic')
        }),
        ('Campaign Performance', {
            'fields': ('email_campaigns_sent', 'email_open_rate', 'email_click_rate', 'email_conversion_rate')
        }),
        ('Social Media', {
            'fields': ('social_media_posts', 'social_media_engagement', 'social_media_reach')
        }),
        ('ROI Metrics', {
            'fields': ('marketing_spend', 'marketing_revenue', 'marketing_roi')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(AIPerformanceMetrics)
class AIPerformanceMetricsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_recommendations_shown', 'recommendations_clicked', 'recommendations_converted', 'recommendation_conversion_rate']
    list_filter = ['date']
    search_fields = ['date']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Date', {
            'fields': ('date',)
        }),
        ('Recommendation Engine', {
            'fields': ('total_recommendations_shown', 'recommendations_clicked', 'recommendations_converted', 'recommendation_click_rate', 'recommendation_conversion_rate')
        }),
        ('Personalization', {
            'fields': ('personalized_content_views', 'personalization_engagement_rate', 'personalization_conversion_rate')
        }),
        ('Model Performance', {
            'fields': ('decision_tree_accuracy', 'association_rules_confidence', 'model_prediction_count')
        }),
        ('Business Impact', {
            'fields': ('ai_driven_revenue', 'ai_driven_orders', 'ai_improvement_rate')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(AnalyticsReport)
class AnalyticsReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'start_date', 'end_date', 'generated_by', 'is_automated', 'created_at']
    list_filter = ['report_type', 'is_automated', 'created_at', 'generated_by']
    search_fields = ['name', 'generated_by__username']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Report Information', {
            'fields': ('name', 'report_type', 'is_automated')
        }),
        ('Date Range', {
            'fields': ('start_date', 'end_date')
        }),
        ('Generation Details', {
            'fields': ('generated_by', 'file_path')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
