from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.utils.html import escape
from django.core.cache import cache
from item.models import Product, Category, Subcategory, Brand
import json
import hashlib

def search(request):
    """Main search view with security improvements"""
    query = request.GET.get('q', '').strip()
    
    # Security: Limit query length
    if len(query) > 100:
        query = query[:100]
    
    # Security: Escape query to prevent XSS
    query = escape(query)
    
    products = []
    
    if query and len(query) >= 2:  # Minimum query length
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(sku__icontains=query)
        ).filter(is_active=True).select_related('category', 'brand')[:50]  # Limit results
    
    context = {
        'query': query,
        'products': products,
    }
    
    return render(request, 'search/results.html', context)

def search_autocomplete(request):
    """Legacy autocomplete endpoint - redirects to suggestions"""
    return search_suggestions(request)

@require_http_methods(["GET"])
def search_suggestions(request):
    """API endpoint for search suggestions with security improvements"""
    query = request.GET.get('q', '').strip()
    
    # Security: Limit query length
    if len(query) > 50:
        query = query[:50]
    
    # Security: Escape query to prevent XSS
    query = escape(query)
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    # Rate limiting using cache
    client_ip = request.META.get('REMOTE_ADDR', 'unknown')
    cache_key = f'search_suggestions_{hashlib.md5(client_ip.encode()).hexdigest()}'
    
    # Check rate limit (max 10 requests per minute)
    request_count = cache.get(cache_key, 0)
    if request_count >= 10:
        return JsonResponse({'suggestions': [], 'rate_limited': True})
    
    # Increment counter
    cache.set(cache_key, request_count + 1, 60)  # 60 seconds
    
    suggestions = []
    
    # Product suggestions
    products = Product.objects.filter(
        Q(name__icontains=query) | 
        Q(description__icontains=query) |
        Q(sku__icontains=query)
    ).filter(is_active=True)[:5]
    
    for product in products:
        suggestions.append({
            'type': 'product',
            'title': escape(product.name),
            'subtitle': f"${product.price}",
            'url': f"/item/{product.id}/",
            'image': product.images.first().image.url if product.images.exists() else None
        })
    
    # Category suggestions
    categories = Category.objects.filter(
        Q(name__icontains=query) | 
        Q(description__icontains=query)
    ).filter(is_active=True)[:3]
    
    for category in categories:
        suggestions.append({
            'type': 'category',
            'title': escape(category.name),
            'subtitle': f"{category.products.count()} products",
            'url': f"/item/category/{category.slug}/",
            'image': category.image.url if hasattr(category, 'image') and category.image else None
        })
    
    # Brand suggestions
    brands = Brand.objects.filter(
        name__icontains=query
    )[:3]
    
    for brand in brands:
        suggestions.append({
            'type': 'brand',
            'title': escape(brand.name),
            'subtitle': f"{brand.products.count()} products",
            'url': f"/item/brand/{brand.slug}/",
            'image': brand.logo.url if hasattr(brand, 'logo') and brand.logo else None
        })
    
    # Subcategory suggestions
    subcategories = Subcategory.objects.filter(
        Q(name__icontains=query) | 
        Q(description__icontains=query)
    ).filter(is_active=True)[:3]
    
    for subcategory in subcategories:
        suggestions.append({
            'type': 'subcategory',
            'title': escape(subcategory.name),
            'subtitle': f"{escape(subcategory.category.name)} • {subcategory.products.count()} products",
            'url': f"/item/category/{subcategory.category.slug}/{subcategory.slug}/",
            'image': None
        })
    
    return JsonResponse({'suggestions': suggestions})