from django.db import models
from django.contrib.auth.models import User
from item.models import Product, Category

class SearchFilter(models.Model):
    """Store user search filter preferences"""
    FILTER_TYPE_CHOICES = [
        ('price_range', 'Price Range'),
        ('brand', 'Brand'),
        ('rating', 'Rating'),
        ('category', 'Category'),
        ('availability', 'Availability'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    filter_type = models.CharField(max_length=20, choices=FILTER_TYPE_CHOICES)
    filter_value = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'filter_type', 'filter_value']
    
    def __str__(self):
        return f"{self.user.username if self.user else 'Anonymous'} - {self.filter_type}: {self.filter_value}"

class SearchHistory(models.Model):
    """Track user search history for analytics and personalization"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    query = models.CharField(max_length=200)
    filters_applied = models.JSONField(default=dict)
    results_count = models.PositiveIntegerField()
    clicked_results = models.JSONField(default=list)  # Product IDs that were clicked
    session_id = models.CharField(max_length=100, blank=True)  # For anonymous users
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"'{self.query}' - {self.results_count} results - {self.created_at}"

class ProductView(models.Model):
    """Track product views for analytics and recommendations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=100, blank=True)  # For anonymous users
    referrer = models.CharField(max_length=200, blank=True)  # Where they came from
    time_spent = models.PositiveIntegerField(default=0)  # Time spent viewing in seconds
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'product', 'session_id', 'created_at']
    
    def __str__(self):
        return f"{self.user.username if self.user else 'Anonymous'} viewed {self.product.name}"

class SearchSuggestion(models.Model):
    """Store popular search suggestions and autocomplete data"""
    query = models.CharField(max_length=200, unique=True)
    popularity_score = models.PositiveIntegerField(default=0)
    category_id = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-popularity_score', 'query']
    
    def __str__(self):
        return f"'{self.query}' (score: {self.popularity_score})"