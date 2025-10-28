from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Sum, Count, Avg
import uuid

class Category(models.Model):
    """Main product categories for AuroraMart e-commerce"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, help_text="URL-friendly version of name")
    description = models.TextField(blank=True, help_text="Category description for SEO")
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0, help_text="Display order")
    
    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name

class Subcategory(models.Model):
    """Subcategories within main categories"""
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['category', 'slug']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"

class Brand(models.Model):
    """Product brands"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    """Main product model - 500 SKUs for AuroraMart"""
    sku = models.CharField(max_length=50, unique=True, help_text="Stock Keeping Unit")
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    
    # Categorization
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, related_name='products', blank=True, null=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products', blank=True, null=True)
    
    # Inventory
    stock_quantity = models.PositiveIntegerField(default=0)
    reorder_threshold = models.PositiveIntegerField(default=10)
    
    # Ratings & Reviews (computed fields - will be updated via signals)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, validators=[MinValueValidator(0), MaxValueValidator(5)])
    review_count = models.PositiveIntegerField(default=0)
    
    # SEO & Display
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', '-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active', 'is_featured']),
            models.Index(fields=['brand', 'is_active']),
            models.Index(fields=['price']),
            models.Index(fields=['average_rating']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate model data"""
        super().clean()
        
        # Validate discount price is less than regular price
        if self.discount_price and self.discount_price >= self.price:
            raise ValidationError('Discount price must be less than regular price')
        
        # Validate subcategory belongs to the same category
        if self.subcategory and self.subcategory.category != self.category:
            raise ValidationError('Subcategory must belong to the selected category')
    
    def save(self, *args, **kwargs):
        """Override save to ensure data consistency"""
        self.full_clean() # Call full_clean for model-level validation
        super().save(*args, **kwargs)
    
    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock_quantity > 0
    
    @property
    def current_price(self):
        """Return current selling price (discount if available)"""
        return self.discount_price if self.discount_price and self.discount_price < self.price else self.price
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage"""
        if self.discount_price and self.price > 0 and self.discount_price < self.price:
            return round(((self.price - self.discount_price) / self.price) * 100)
        return 0
    
    @property
    def is_low_stock(self):
        """Check if product is low on stock"""
        return self.stock_quantity <= self.reorder_threshold
    
    def update_rating_stats(self):
        """Update average rating and review count from reviews"""
        from django.db.models import Avg, Count
        stats = self.reviews.aggregate(
            avg_rating=Avg('rating'),
            count=Count('id')
        )
        self.average_rating = stats['avg_rating'] or 0
        self.review_count = stats['count'] or 0
        self.save(update_fields=['average_rating', 'review_count'])

class ProductImage(models.Model):
    """Multiple images per product"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['is_primary', 'sort_order']
    
    def __str__(self):
        return f"{self.product.name} - Image {self.sort_order}"

class ProductSpecification(models.Model):
    """Product specifications/attributes"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specifications')
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=200)
    sort_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['sort_order']
    
    def __str__(self):
        return f"{self.product.name} - {self.name}: {self.value}"

class ProductReview(models.Model):
    """Product reviews and ratings"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200)
    comment = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['product', 'user']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'rating']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating} stars)"
    
    def save(self, *args, **kwargs):
        """Override save to update product rating stats"""
        super().save(*args, **kwargs)
        self.product.update_rating_stats()
    
    def delete(self, *args, **kwargs):
        """Override delete to update product rating stats"""
        product = self.product
        super().delete(*args, **kwargs)
        product.update_rating_stats()

# Signals to automatically update product rating stats
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=ProductReview)
def update_product_rating_on_save(sender, instance, **kwargs):
    """Update product rating stats when review is saved"""
    instance.product.update_rating_stats()

@receiver(post_delete, sender=ProductReview)
def update_product_rating_on_delete(sender, instance, **kwargs):
    """Update product rating stats when review is deleted"""
    instance.product.update_rating_stats()