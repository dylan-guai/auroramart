from django.contrib import admin
from .models import Category, Subcategory, Brand, Product, ProductImage, ProductSpecification, ProductReview

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'sort_order']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'slug', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'brand', 'price', 'current_price', 'stock_quantity', 'is_featured', 'is_active']
    list_filter = ['category', 'brand', 'is_featured', 'is_active']
    search_fields = ['name', 'sku', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at', 'average_rating', 'review_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'sku', 'slug', 'description', 'short_description')
        }),
        ('Pricing', {
            'fields': ('price', 'discount_price')
        }),
        ('Categorization', {
            'fields': ('category', 'subcategory', 'brand')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'reorder_threshold')
        }),
        ('Display & SEO', {
            'fields': ('is_featured', 'is_active', 'meta_title', 'meta_description')
        }),
        ('Ratings', {
            'fields': ('average_rating', 'review_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'is_primary', 'sort_order']
    list_filter = ['is_primary']
    ordering = ['product', 'is_primary', 'sort_order']

@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'value', 'sort_order']
    ordering = ['product', 'sort_order']

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'is_verified_purchase', 'created_at']
    list_filter = ['rating', 'is_verified_purchase', 'created_at']
    search_fields = ['product__name', 'user__username', 'title', 'comment']
    readonly_fields = ['created_at', 'updated_at']