from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, F, Case, When, DecimalField, Count, Avg
from django.core.paginator import Paginator
from django.contrib import messages
import logging

from .models import Product, Category, Subcategory, Brand, ProductReview
from profiles.models import Profile
from checkout.models import Cart, CartItem, OrderItem
from core.ml_service import ml_service

logger = logging.getLogger(__name__)

def product_list(request):
    """Display all products with filtering and sorting - optimized"""
    # Base queryset with proper filtering and optimization
    products = Product.objects.select_related('category', 'brand').filter(is_active=True, stock_quantity__gt=0)
    categories = Category.objects.filter(is_active=True)
    
    # Get filter parameters
    category_id = request.GET.get('category')
    search_query = request.GET.get('search')
    sort_by = request.GET.get('sort', 'name')
    page = request.GET.get('page', 1)
    
    # Apply filters
    current_category = None
    if category_id:
        try:
            current_category = Category.objects.get(id=category_id, is_active=True)
            products = products.filter(category=current_category)
        except (Category.DoesNotExist, ValueError):
            # Handle invalid category_id gracefully
            current_category = None
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(sku__icontains=search_query)
        )
    
    # Apply sorting with proper database fields
    if sort_by == 'price_low':
        products = products.annotate(
            current_price_field=Case(
                When(discount_price__isnull=False, then=F('discount_price')),
                default=F('price'),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        ).order_by('current_price_field')
    elif sort_by == 'price_high':
        products = products.annotate(
            current_price_field=Case(
                When(discount_price__isnull=False, then=F('discount_price')),
                default=F('price'),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        ).order_by('-current_price_field')
    elif sort_by == 'rating':
        # Sort by average_rating field (computed field) with fallback to review count
        products = products.order_by('-average_rating', '-review_count')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'popular':
        # Sort by review count and creation date (since we don't have ProductView model)
        products = products.annotate(
            popularity_score=Count('reviews')
        ).order_by('-popularity_score', '-created_at')
    elif sort_by == '-name':
        products = products.order_by('-name')
    else:
        products = products.order_by('name')
    
    # Add prefetch_related for images before pagination
    products = products.prefetch_related('images')
    
    # Add pagination
    paginator = Paginator(products, 20)  # 20 products per page
    products_page = paginator.get_page(page)
    
    context = {
        'products': products_page,
        'categories': categories,
        'current_category': current_category,
        'search_query': search_query,
        'sort_by': sort_by,
        'total_products': products.count(),
    }
    
    return render(request, 'item/product_list.html', context)

def product_detail(request, product_id):
    """Display detailed product information with AI-powered recommendations"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Paginate reviews
    reviews = ProductReview.objects.filter(product=product).order_by('-created_at')
    paginator = Paginator(reviews, 10)  # 10 reviews per page
    page = request.GET.get('page')
    reviews_page = paginator.get_page(page)
    
    # Get related products from same category - optimized query
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True,
        stock_quantity__gt=0
    ).exclude(id=product_id).select_related('category', 'brand')[:4]
    
    # AI-Powered Recommendations
    recommended_products = []
    frequently_bought_together = []
    
    try:
        # Get frequently bought together recommendations
        fbt_recommendations = ml_service.get_frequently_bought_together(product.sku, top_n=3)
        
        if fbt_recommendations:
            # Get product objects for the recommended SKUs
            recommended_skus = [rec[0] for rec in fbt_recommendations]
            recommended_products = Product.objects.filter(
                sku__in=recommended_skus,
                is_active=True,
                stock_quantity__gt=0
            ).select_related('category', 'brand')
            
            # Create list with confidence scores
            frequently_bought_together = []
            for rec_product in recommended_products:
                for sku, confidence in fbt_recommendations:
                    if rec_product.sku == sku:
                        frequently_bought_together.append({
                            'product': rec_product,
                            'confidence': confidence
                        })
                        break
        
        # If no AI recommendations, fall back to related products
        if not recommended_products:
            recommended_products = related_products[:3]
            
    except Exception as e:
        logger.error(f"AI recommendation error: {e}")
        recommended_products = related_products[:3]
    
    # Check if user has purchased this product (for review verification)
    has_purchased = False
    if request.user.is_authenticated:
        has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            product=product,
            order__status='delivered'
        ).exists()
    
    # Check if product is in user's wishlist
    is_wished = False
    if request.user.is_authenticated:
        from profiles.models import Wishlist
        is_wished = Wishlist.objects.filter(
            user=request.user,
            product=product
        ).exists()
    
    context = {
        'product': product,
        'reviews': reviews_page,
        'related_products': related_products,
        'recommended_products': recommended_products,
        'frequently_bought_together': frequently_bought_together,
        'has_purchased': has_purchased,
        'is_wished': is_wished,
    }
    
    return render(request, 'item/product_detail.html', context)

def add_to_cart(request, product_id):
    """Add product to user's cart - supports both logged in and logged out users"""
    if request.method != 'POST':
        return redirect('item:product_detail', product_id=product_id)
    
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True, stock_quantity__gt=0)
    except ValueError:
        logger.error(f"Invalid product ID provided: {product_id}")
        messages.error(request, "Invalid product ID.")
        return redirect('item:product_list')
    except Product.DoesNotExist:
        logger.warning(f"Product not found or inactive: {product_id}")
        messages.error(request, "Product not found or no longer available.")
        return redirect('item:product_list')
    
    # Get quantity from request with proper validation
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid quantity provided: {request.POST.get('quantity')}")
        messages.error(request, "Invalid quantity specified.")
        return redirect('item:product_detail', product_id=product_id)
    
    # Validate quantity
    if quantity <= 0:
        logger.warning(f"Non-positive quantity provided: {quantity}")
        messages.error(request, "Quantity must be greater than zero.")
        return redirect('item:product_detail', product_id=product_id)
    
    if quantity > 99:  # Reasonable limit
        logger.warning(f"Excessive quantity requested: {quantity}")
        messages.error(request, "Maximum quantity per item is 99.")
        return redirect('item:product_detail', product_id=product_id)
    
    # Check stock availability
    if quantity > product.stock_quantity:
        logger.info(f"Stock limit exceeded for product {product_id}")
        messages.warning(request, f"Only {product.stock_quantity} items available in stock.")
        return redirect('item:product_detail', product_id=product_id)
    
    if request.user.is_authenticated:
        # Logged in user - add to database cart
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            logger.error(f"Profile not found for user: {request.user.username}")
            messages.error(request, "Profile not found. Please complete your profile.")
            return redirect('profiles:profile')

        try:
            cart, created = Cart.objects.get_or_create(buyer=profile)
        except Exception as e:
            logger.error(f"Error creating/retrieving cart for user {request.user.username}: {e}")
            messages.error(request, "Error accessing your cart. Please try again.")
            return redirect('item:product_detail', product_id=product_id)
        
        # Check if adding this quantity would exceed stock
        try:
            existing_item = CartItem.objects.filter(cart=cart, product=product).first()
            current_quantity = existing_item.quantity if existing_item else 0
            
            if current_quantity + quantity > product.stock_quantity:
                logger.info(f"Stock limit exceeded for product {product_id} by user {request.user.username}")
                messages.warning(request, f"Only {product.stock_quantity} items available in stock. You already have {current_quantity} in your cart.")
                return redirect('item:product_detail', product_id=product_id)
            
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart, 
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            logger.info(f"Product {product_id} added to cart for user {request.user.username}, quantity: {quantity}")
            messages.success(request, f"{product.name} added to cart!")
            
        except Exception as e:
            logger.error(f"Error adding product {product_id} to cart for user {request.user.username}: {e}")
            messages.error(request, "Error adding item to cart. Please try again.")
            return redirect('item:product_detail', product_id=product_id)
    
    else:
        # Logged out user - add to session cart
        session_cart = request.session.get('cart', {})
        
        # Check if product already exists in session cart
        if str(product_id) in session_cart:
            current_quantity = session_cart[str(product_id)]
            if current_quantity + quantity > product.stock_quantity:
                messages.warning(request, f"Only {product.stock_quantity} items available in stock. You already have {current_quantity} in your cart.")
                return redirect('item:product_detail', product_id=product_id)
            session_cart[str(product_id)] += quantity
        else:
            session_cart[str(product_id)] = quantity
        
        request.session['cart'] = session_cart
        request.session.modified = True
        
        logger.info(f"Product {product_id} added to session cart, quantity: {quantity}")
        messages.success(request, f"{product.name} added to cart! Please sign in to complete your purchase.")
        
        # Redirect to login with next parameter
        return redirect(f"{reverse('core:login')}?next={reverse('item:product_detail', args=[product_id])}")
    
    return redirect('item:product_detail', product_id=product_id)

@login_required
def add_review(request, product_id):
    """Add product review - with proper validation and verification"""
    if request.method != 'POST':
        return redirect('item:product_detail', product_id=product_id)
    
    product = get_object_or_404(Product, id=product_id, is_active=True)
    rating = request.POST.get('rating')
    title = request.POST.get('title', '').strip()
    comment = request.POST.get('comment', '').strip()
    
    # Validate input
    if not all([rating, title, comment]):
        messages.error(request, "All fields are required.")
        return redirect('item:product_detail', product_id=product_id)
    
    try:
        rating = int(rating)
        if not (1 <= rating <= 5):
            raise ValueError("Invalid rating")
    except (ValueError, TypeError):
        messages.error(request, "Rating must be between 1 and 5.")
        return redirect('item:product_detail', product_id=product_id)
    
    # Check if user has purchased this product
    has_purchased = OrderItem.objects.filter(
        order__user=request.user,
        product=product,
        order__status='delivered'
    ).exists()
    
    # Create or update review
    review, created = ProductReview.objects.update_or_create(
        product=product,
        user=request.user,
        defaults={
            'rating': rating,
            'title': title,
            'comment': comment,
            'is_verified_purchase': has_purchased
        }
    )
    
    if created:
        messages.success(request, "Thank you for your review!")
    else:
        messages.success(request, "Your review has been updated!")
    
    return redirect('item:product_detail', product_id=product_id)

def category_detail(request, category_slug):
    """Display products in a specific category with breadcrumbs"""
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    
    # Get products in this category
    products = Product.objects.filter(
        category=category,
        is_active=True,
        stock_quantity__gt=0
    ).select_related('category', 'brand').prefetch_related('images')
    
    # Apply sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_low':
        products = products.annotate(
            current_price_field=Case(
                When(discount_price__isnull=False, then=F('discount_price')),
                default=F('price'),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        ).order_by('current_price_field')
    elif sort_by == 'price_high':
        products = products.annotate(
            current_price_field=Case(
                When(discount_price__isnull=False, then=F('discount_price')),
                default=F('price'),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        ).order_by('-current_price_field')
    elif sort_by == 'rating':
        # Sort by average_rating field (computed field) with fallback to review count
        products = products.order_by('-average_rating', '-review_count')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'popular':
        # Sort by review count and creation date (since we don't have ProductView model)
        products = products.annotate(
            popularity_score=Count('reviews')
        ).order_by('-popularity_score', '-created_at')
    elif sort_by == '-name':
        products = products.order_by('-name')
    else:
        products = products.order_by('name')
    
    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Breadcrumbs
    breadcrumbs = [
        {'name': 'Home', 'url': '/'},
        {'name': category.name, 'url': None}
    ]
    
    context = {
        'category': category,
        'products': page_obj,
        'subcategories': category.subcategories.filter(is_active=True),
        'breadcrumbs': breadcrumbs,
        'sort_by': sort_by,
        'total_products': products.count(),
    }
    
    return render(request, 'item/category_detail.html', context)

def subcategory_detail(request, category_slug, subcategory_slug):
    """Display products in a specific subcategory with breadcrumbs"""
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    subcategory = get_object_or_404(Subcategory, slug=subcategory_slug, category=category, is_active=True)
    
    # Get products in this subcategory
    products = Product.objects.filter(
        subcategory=subcategory,
        is_active=True,
        stock_quantity__gt=0
    ).select_related('category', 'subcategory', 'brand').prefetch_related('images')
    
    # Apply sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_low':
        products = products.annotate(
            current_price_field=Case(
                When(discount_price__isnull=False, then=F('discount_price')),
                default=F('price'),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        ).order_by('current_price_field')
    elif sort_by == 'price_high':
        products = products.annotate(
            current_price_field=Case(
                When(discount_price__isnull=False, then=F('discount_price')),
                default=F('price'),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        ).order_by('-current_price_field')
    elif sort_by == 'rating':
        # Sort by average_rating field (computed field) with fallback to review count
        products = products.order_by('-average_rating', '-review_count')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'popular':
        # Sort by review count and creation date (since we don't have ProductView model)
        products = products.annotate(
            popularity_score=Count('reviews')
        ).order_by('-popularity_score', '-created_at')
    elif sort_by == '-name':
        products = products.order_by('-name')
    else:
        products = products.order_by('name')
    
    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Breadcrumbs
    breadcrumbs = [
        {'name': 'Home', 'url': '/'},
        {'name': category.name, 'url': f'/item/category/{category.slug}/'},
        {'name': subcategory.name, 'url': None}
    ]
    
    context = {
        'category': category,
        'subcategory': subcategory,
        'products': page_obj,
        'breadcrumbs': breadcrumbs,
        'sort_by': sort_by,
        'total_products': products.count(),
    }
    
    return render(request, 'item/subcategory_detail.html', context)