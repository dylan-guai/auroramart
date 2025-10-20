from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import uuid


class AnalyticsDashboard(models.Model):
    """Main analytics dashboard configuration"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Analytics Dashboard'
        verbose_name_plural = 'Analytics Dashboards'
    
    def __str__(self):
        return self.name


class AnalyticsWidget(models.Model):
    """Individual widgets for the analytics dashboard"""
    WIDGET_TYPES = [
        ('chart', 'Chart'),
        ('metric', 'Metric'),
        ('table', 'Table'),
        ('gauge', 'Gauge'),
        ('trend', 'Trend'),
        ('map', 'Map'),
    ]
    
    CHART_TYPES = [
        ('line', 'Line Chart'),
        ('bar', 'Bar Chart'),
        ('pie', 'Pie Chart'),
        ('doughnut', 'Doughnut Chart'),
        ('area', 'Area Chart'),
        ('scatter', 'Scatter Plot'),
    ]
    
    dashboard = models.ForeignKey(AnalyticsDashboard, on_delete=models.CASCADE, related_name='widgets')
    name = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    chart_type = models.CharField(max_length=20, choices=CHART_TYPES, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    data_source = models.CharField(max_length=100)  # Function name to get data
    position_x = models.PositiveIntegerField(default=0)
    position_y = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(default=4)
    height = models.PositiveIntegerField(default=3)
    refresh_interval = models.PositiveIntegerField(default=300)  # seconds
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['position_y', 'position_x']
        verbose_name = 'Analytics Widget'
        verbose_name_plural = 'Analytics Widgets'
    
    def __str__(self):
        return f"{self.dashboard.name} - {self.name}"


class BusinessMetrics(models.Model):
    """Daily business metrics for analytics"""
    date = models.DateField(unique=True)
    
    # Revenue Metrics
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Order Metrics
    total_orders = models.PositiveIntegerField(default=0)
    completed_orders = models.PositiveIntegerField(default=0)
    cancelled_orders = models.PositiveIntegerField(default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Customer Metrics
    new_customers = models.PositiveIntegerField(default=0)
    returning_customers = models.PositiveIntegerField(default=0)
    total_customers = models.PositiveIntegerField(default=0)
    customer_retention_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Product Metrics
    products_sold = models.PositiveIntegerField(default=0)
    unique_products_sold = models.PositiveIntegerField(default=0)
    top_selling_category = models.CharField(max_length=100, blank=True)
    
    # Conversion Metrics
    page_views = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cart_abandonment_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Loyalty Metrics
    loyalty_points_earned = models.PositiveIntegerField(default=0)
    loyalty_points_redeemed = models.PositiveIntegerField(default=0)
    loyalty_redemptions = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name = 'Business Metrics'
        verbose_name_plural = 'Business Metrics'
    
    def __str__(self):
        return f"Business Metrics - {self.date}"


class CustomerAnalytics(models.Model):
    """Customer behavior and segmentation analytics"""
    date = models.DateField()
    
    # Demographics
    age_distribution = models.JSONField(default=dict)
    gender_distribution = models.JSONField(default=dict)
    location_distribution = models.JSONField(default=dict)
    
    # Behavior Metrics
    average_session_duration = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    pages_per_session = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    bounce_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Purchase Behavior
    purchase_frequency = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_purchase_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    customer_lifetime_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Segmentation
    high_value_customers = models.PositiveIntegerField(default=0)
    medium_value_customers = models.PositiveIntegerField(default=0)
    low_value_customers = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['date']
        ordering = ['-date']
        verbose_name = 'Customer Analytics'
        verbose_name_plural = 'Customer Analytics'
    
    def __str__(self):
        return f"Customer Analytics - {self.date}"


class ProductAnalytics(models.Model):
    """Product performance and inventory analytics"""
    date = models.DateField()
    
    # Sales Performance
    total_products_sold = models.PositiveIntegerField(default=0)
    revenue_by_category = models.JSONField(default=dict)
    top_selling_products = models.JSONField(default=list)
    low_selling_products = models.JSONField(default=list)
    
    # Inventory Metrics
    total_inventory_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    low_stock_products = models.PositiveIntegerField(default=0)
    out_of_stock_products = models.PositiveIntegerField(default=0)
    inventory_turnover_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Product Performance
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_reviews = models.PositiveIntegerField(default=0)
    products_with_reviews = models.PositiveIntegerField(default=0)
    
    # Search Analytics
    most_searched_products = models.JSONField(default=list)
    search_no_results = models.PositiveIntegerField(default=0)
    search_conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['date']
        ordering = ['-date']
        verbose_name = 'Product Analytics'
        verbose_name_plural = 'Product Analytics'
    
    def __str__(self):
        return f"Product Analytics - {self.date}"


class MarketingAnalytics(models.Model):
    """Marketing campaign and channel performance"""
    date = models.DateField()
    
    # Traffic Sources
    organic_traffic = models.PositiveIntegerField(default=0)
    paid_traffic = models.PositiveIntegerField(default=0)
    social_traffic = models.PositiveIntegerField(default=0)
    direct_traffic = models.PositiveIntegerField(default=0)
    referral_traffic = models.PositiveIntegerField(default=0)
    
    # Campaign Performance
    email_campaigns_sent = models.PositiveIntegerField(default=0)
    email_open_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    email_click_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    email_conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Social Media
    social_media_posts = models.PositiveIntegerField(default=0)
    social_media_engagement = models.PositiveIntegerField(default=0)
    social_media_reach = models.PositiveIntegerField(default=0)
    
    # ROI Metrics
    marketing_spend = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    marketing_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    marketing_roi = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['date']
        ordering = ['-date']
        verbose_name = 'Marketing Analytics'
        verbose_name_plural = 'Marketing Analytics'
    
    def __str__(self):
        return f"Marketing Analytics - {self.date}"


class AIPerformanceMetrics(models.Model):
    """AI/ML model performance and impact metrics"""
    date = models.DateField()
    
    # Recommendation Engine
    total_recommendations_shown = models.PositiveIntegerField(default=0)
    recommendations_clicked = models.PositiveIntegerField(default=0)
    recommendations_converted = models.PositiveIntegerField(default=0)
    recommendation_click_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    recommendation_conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Personalization
    personalized_content_views = models.PositiveIntegerField(default=0)
    personalization_engagement_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    personalization_conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Model Performance
    decision_tree_accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    association_rules_confidence = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    model_prediction_count = models.PositiveIntegerField(default=0)
    
    # Business Impact
    ai_driven_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ai_driven_orders = models.PositiveIntegerField(default=0)
    ai_improvement_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['date']
        ordering = ['-date']
        verbose_name = 'AI Performance Metrics'
        verbose_name_plural = 'AI Performance Metrics'
    
    def __str__(self):
        return f"AI Performance Metrics - {self.date}"


class AnalyticsReport(models.Model):
    """Generated analytics reports"""
    REPORT_TYPES = [
        ('daily', 'Daily Report'),
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
        ('quarterly', 'Quarterly Report'),
        ('yearly', 'Yearly Report'),
        ('custom', 'Custom Report'),
    ]
    
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    is_automated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Analytics Report'
        verbose_name_plural = 'Analytics Reports'
    
    def __str__(self):
        return f"{self.name} ({self.report_type})"
