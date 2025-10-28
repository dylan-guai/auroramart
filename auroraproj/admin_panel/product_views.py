from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg, F
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
import csv
import io

from online_store.item.models import Product, Category, Subcategory, Brand, ProductImage
from online_store.checkout.models import Order, OrderItem
from admin_panel.decorators import admin_required, role_required
from admin_panel.models import AuditLog

@admin_required
@role_required(['Admin', 'Merchandiser'])
def product_list(request):
    """Product catalog management"""
    products = Product.objects.select_related('category', 'subcategory', 'brand').prefetch_related('images').all()
    
    # Filters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    brand_filter = request.GET.get('brand', '')
    status_filter = request.GET.get('status', '')
    sort_by = request.GET.get('sort', 'name')
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if category_filter:
        products = products.filter(category_id=category_filter)
    
    if brand_filter:
        products = products.filter(brand_id=brand_filter)
    
    if status_filter == 'active':
        products = products.filter(is_active=True)
    elif status_filter == 'inactive':
        products = products.filter(is_active=False)
    elif status_filter == 'low_stock':
        products = products.filter(stock_quantity__lte=F('reorder_threshold'))
    elif status_filter == 'out_of_stock':
        products = products.filter(stock_quantity=0)
    
    # Apply sorting
    if sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == '-name':
        products = products.order_by('-name')
    elif sort_by == 'price':
        products = products.order_by('price')
    elif sort_by == '-price':
        products = products.order_by('-price')
    elif sort_by == 'created':
        products = products.order_by('created_at')
    elif sort_by == '-created':
        products = products.order_by('-created_at')
    elif sort_by == 'stock':
        products = products.order_by('stock_quantity')
    elif sort_by == '-stock':
        products = products.order_by('-stock_quantity')
    else:
        products = products.order_by('name')
    
    # Pagination
    paginator = Paginator(products, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    categories = Category.objects.all()
    brands = Brand.objects.all()
    
    # Statistics
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    low_stock_products = Product.objects.filter(stock_quantity__lte=F('reorder_threshold')).count()
    out_of_stock_products = Product.objects.filter(stock_quantity=0).count()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'brand_filter': brand_filter,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'categories': categories,
        'brands': brands,
        'total_products': total_products,
        'active_products': active_products,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
    }
    
    return render(request, 'admin_panel/product_list.html', context)

@admin_required
@role_required(['Admin', 'Merchandiser'])
def product_detail(request, product_id):
    """Product detail view for admin"""
    product = get_object_or_404(Product, id=product_id)
    
    # Get product images
    images = product.images.all()
    
    # Get sales statistics
    orderitem = OrderItem.objects.filter(product=product)
    total_sold = orderitem.aggregate(total=Sum('quantity'))['total'] or 0
    total_revenue = orderitem.aggregate(total=Sum('price_at_purchase'))['total'] or 0
    
    # Get recent orders
    recent_orders = Order.objects.filter(orderitem__product=product).distinct().order_by('-created_at')[:10]
    
    context = {
        'product': product,
        'images': images,
        'total_sold': total_sold,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
    }
    
    return render(request, 'admin_panel/product_detail.html', context)

@admin_required
@role_required(['Admin', 'Merchandiser'])
def product_create(request):
    """Create new product"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            sku = request.POST.get('sku')
            description = request.POST.get('description')
            short_description = request.POST.get('short_description')
            price = request.POST.get('price')
            discount_price = request.POST.get('discount_price') or None
            stock_quantity = request.POST.get('stock_quantity')
            reorder_threshold = request.POST.get('reorder_threshold')
            category_id = request.POST.get('category')
            subcategory_id = request.POST.get('subcategory')
            brand_id = request.POST.get('brand')
            is_active = request.POST.get('is_active') == 'on'
            
            # Validate required fields
            if not all([name, sku, price, stock_quantity, reorder_threshold]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('admin_panel:product_create')
            
            # Check if SKU already exists
            if Product.objects.filter(sku=sku).exists():
                messages.error(request, 'A product with this SKU already exists.')
                return redirect('admin_panel:product_create')
            
            # Create product
            product = Product.objects.create(
                name=name,
                sku=sku,
                description=description,
                short_description=short_description,
                price=float(price),
                discount_price=float(discount_price) if discount_price else None,
                stock_quantity=int(stock_quantity),
                reorder_threshold=int(reorder_threshold),
                category_id=category_id if category_id else None,
                subcategory_id=subcategory_id if subcategory_id else None,
                brand_id=brand_id if brand_id else None,
                is_active=is_active
            )
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='PRODUCT_CREATED',
                description=f'Created product: {product.name}. SKU: {product.sku}, Price: ${product.price}'
            )
            
            messages.success(request, f'Product "{product.name}" created successfully.')
            return redirect('admin_panel:product_detail', product_id=product.id)
            
        except Exception as e:
            messages.error(request, f'Error creating product: {str(e)}')
    
    # Get form options
    categories = Category.objects.all()
    subcategories = Subcategory.objects.all()
    brands = Brand.objects.all()
    
    context = {
        'categories': categories,
        'subcategories': subcategories,
        'brands': brands,
    }
    
    return render(request, 'admin_panel/product_create.html', context)

@admin_required
@role_required(['Admin', 'Merchandiser'])
def product_edit(request, product_id):
    """Edit existing product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        try:
            # Get form data
            product.name = request.POST.get('name')
            product.sku = request.POST.get('sku')
            product.description = request.POST.get('description')
            product.short_description = request.POST.get('short_description')
            product.price = float(request.POST.get('price'))
            product.discount_price = float(request.POST.get('discount_price')) if request.POST.get('discount_price') else None
            product.stock_quantity = int(request.POST.get('stock_quantity'))
            product.reorder_threshold = int(request.POST.get('reorder_threshold'))
            product.category_id = request.POST.get('category') if request.POST.get('category') else None
            product.subcategory_id = request.POST.get('subcategory') if request.POST.get('subcategory') else None
            product.brand_id = request.POST.get('brand') if request.POST.get('brand') else None
            product.is_active = request.POST.get('is_active') == 'on'
            
            # Check if SKU already exists (excluding current product)
            if Product.objects.filter(sku=product.sku).exclude(id=product.id).exists():
                messages.error(request, 'A product with this SKU already exists.')
                return redirect('admin_panel:product_edit', product_id=product.id)
            
            product.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='PRODUCT_UPDATED',
                description=f'Updated product: {product.name}. SKU: {product.sku}, Price: ${product.price}'
            )
            
            messages.success(request, f'Product "{product.name}" updated successfully.')
            return redirect('admin_panel:product_detail', product_id=product.id)
            
        except Exception as e:
            messages.error(request, f'Error updating product: {str(e)}')
    
    # Get form options
    categories = Category.objects.all()
    subcategories = Subcategory.objects.all()
    brands = Brand.objects.all()
    
    context = {
        'product': product,
        'categories': categories,
        'subcategories': subcategories,
        'brands': brands,
    }
    
    return render(request, 'admin_panel/product_edit.html', context)

@admin_required
@role_required(['Admin', 'Merchandiser'])
def product_delete(request, product_id):
    """Soft delete product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        try:
            # Soft delete by setting is_active to False
            product.is_active = False
            product.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='PRODUCT_DELETED',
                description=f'Deleted product: {product.name}. SKU: {product.sku}'
            )
            
            messages.success(request, f'Product "{product.name}" has been deactivated.')
            return redirect('admin_panel:product_list')
            
        except Exception as e:
            messages.error(request, f'Error deleting product: {str(e)}')
    
    context = {
        'product': product,
    }
    
    return render(request, 'admin_panel/product_delete.html', context)

@admin_required
@role_required(['Admin', 'Merchandiser'])
def category_list(request):
    """Category management"""
    categories = Category.objects.prefetch_related('subcategories').all()
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'admin_panel/category_list.html', context)

@admin_required
@role_required(['Admin', 'Merchandiser'])
def category_create(request):
    """Create new category"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description')
            is_active = request.POST.get('is_active') == 'on'
            
            if not name:
                messages.error(request, 'Category name is required.')
                return redirect('admin_panel:category_create')
            
            category = Category.objects.create(
                name=name,
                description=description,
                is_active=is_active
            )
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='CATEGORY_CREATED',
                description=f'Created category: {category.name}'
            )
            
            messages.success(request, f'Category "{category.name}" created successfully.')
            return redirect('admin_panel:category_list')
            
        except Exception as e:
            messages.error(request, f'Error creating category: {str(e)}')
    
    return render(request, 'admin_panel/category_create.html')

@admin_required
@role_required(['Admin', 'Merchandiser'])
def category_edit(request, category_id):
    """Edit existing category"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        try:
            category.name = request.POST.get('name')
            category.description = request.POST.get('description')
            category.is_active = request.POST.get('is_active') == 'on'
            category.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='CATEGORY_UPDATED',
                description=f'Updated category: {category.name}'
            )
            
            messages.success(request, f'Category "{category.name}" updated successfully.')
            return redirect('admin_panel:category_list')
            
        except Exception as e:
            messages.error(request, f'Error updating category: {str(e)}')
    
    context = {
        'category': category,
    }
    
    return render(request, 'admin_panel/category_edit.html', context)

@admin_required
@role_required(['Admin', 'Merchandiser'])
def product_bulk_export(request):
    """Export products to CSV"""
    products = Product.objects.select_related('category', 'subcategory', 'brand').all()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'SKU', 'Name', 'Description', 'Short Description', 'Price', 'Discount Price',
        'Stock Quantity', 'Reorder Threshold', 'Category', 'Subcategory', 'Brand',
        'Is Active', 'Created At', 'Updated At'
    ])
    
    for product in products:
        writer.writerow([
            product.sku,
            product.name,
            product.description,
            product.short_description,
            product.price,
            product.discount_price,
            product.stock_quantity,
            product.reorder_threshold,
            product.category.name if product.category else '',
            product.subcategory.name if product.subcategory else '',
            product.brand.name if product.brand else '',
            product.is_active,
            product.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            product.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response

@admin_required
@role_required(['Admin', 'Merchandiser'])
def product_bulk_import(request):
    """Bulk import products from CSV"""
    if request.method == 'POST':
        try:
            csv_file = request.FILES['csv_file']
            
            # Read CSV file
            file_data = csv_file.read().decode('utf-8')
            csv_data = csv.DictReader(io.StringIO(file_data))
            
            success_count = 0
            error_count = 0
            errors = []
            
            for row_num, row in enumerate(csv_data, start=2):
                try:
                    # Validate required fields
                    if not all([row.get('SKU'), row.get('Name'), row.get('Price')]):
                        errors.append(f'Row {row_num}: Missing required fields (SKU, Name, Price)')
                        error_count += 1
                        continue
                    
                    # Check if SKU already exists
                    if Product.objects.filter(sku=row['SKU']).exists():
                        errors.append(f'Row {row_num}: SKU {row["SKU"]} already exists')
                        error_count += 1
                        continue
                    
                    # Create product
                    Product.objects.create(
                        sku=row['SKU'],
                        name=row['Name'],
                        description=row.get('Description', ''),
                        short_description=row.get('Short Description', ''),
                        price=float(row['Price']),
                        discount_price=float(row['Discount Price']) if row.get('Discount Price') else None,
                        stock_quantity=int(row.get('Stock Quantity', 0)),
                        reorder_threshold=int(row.get('Reorder Threshold', 10)),
                        category_id=row.get('Category') if row.get('Category') else None,
                        subcategory_id=row.get('Subcategory') if row.get('Subcategory') else None,
                        brand_id=row.get('Brand') if row.get('Brand') else None,
                        is_active=row.get('Is Active', 'True').lower() == 'true'
                    )
                    
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f'Row {row_num}: {str(e)}')
                    error_count += 1
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='PRODUCT_BULK_IMPORT',
                description=f'Bulk imported products. Success: {success_count}, Errors: {error_count}'
            )
            
            if success_count > 0:
                messages.success(request, f'Successfully imported {success_count} products.')
            
            if error_count > 0:
                messages.warning(request, f'{error_count} products failed to import.')
                # Store errors in session for display
                request.session['import_errors'] = errors[:10]  # Limit to first 10 errors
            
            return redirect('admin_panel:product_list')
            
        except Exception as e:
            messages.error(request, f'Error processing CSV file: {str(e)}')
    
    # Get import errors from session
    import_errors = request.session.pop('import_errors', [])
    
    context = {
        'import_errors': import_errors,
    }
    
    return render(request, 'admin_panel/product_bulk_import.html', context)

@admin_required
@role_required(['Admin', 'Merchandiser', 'analyst'])
def product_performance_dashboard(request):
    """Product Performance Dashboard with KPIs and analytics"""
    
    # Time period filters
    period = request.GET.get('period', '30')  # days
    try:
        period_days = int(period)
    except ValueError:
        period_days = 30
    
    start_date = timezone.now() - timedelta(days=period_days)
    
    # Overall KPIs
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    low_stock_products = Product.objects.filter(stock_quantity__lte=F('reorder_threshold')).count()
    out_of_stock_products = Product.objects.filter(stock_quantity=0).count()
    
    # Sales KPIs for the period
    period_orders = Order.objects.filter(created_at__gte=start_date)
    period_orderitem = OrderItem.objects.filter(order__created_at__gte=start_date)
    
    total_sales_revenue = period_orderitem.aggregate(
        total=Sum('price_at_purchase')
    )['total'] or 0
    
    total_units_sold = period_orderitem.aggregate(
        total=Sum('quantity')
    )['total'] or 0
    
    # Top performing products (by revenue)
    top_products_revenue = Product.objects.annotate(
        period_revenue=Sum(
            'orderitem__price_at_purchase',
            filter=Q(orderitem__order__created_at__gte=start_date)
        ),
        period_quantity=Sum(
            'orderitem__quantity',
            filter=Q(orderitem__order__created_at__gte=start_date)
        )
    ).filter(
        period_revenue__gt=0
    ).order_by('-period_revenue')[:10]
    
    # Top performing products (by quantity sold)
    top_products_quantity = Product.objects.annotate(
        period_revenue=Sum(
            'orderitem__price_at_purchase',
            filter=Q(orderitem__order__created_at__gte=start_date)
        ),
        period_quantity=Sum(
            'orderitem__quantity',
            filter=Q(orderitem__order__created_at__gte=start_date)
        )
    ).filter(
        period_quantity__gt=0
    ).order_by('-period_quantity')[:10]
    
    # Bottom performing products (lowest revenue)
    bottom_products_revenue = Product.objects.annotate(
        period_revenue=Sum(
            'orderitem__price_at_purchase',
            filter=Q(orderitem__order__created_at__gte=start_date)
        ),
        period_quantity=Sum(
            'orderitem__quantity',
            filter=Q(orderitem__order__created_at__gte=start_date)
        )
    ).filter(
        period_revenue__isnull=True
    ).order_by('created_at')[:10]
    
    # Category performance
    category_performance = Category.objects.annotate(
        product_count=Count('products'),
        period_revenue=Sum(
            'products__orderitem__price_at_purchase',
            filter=Q(products__orderitem__order__created_at__gte=start_date)
        ),
        period_quantity=Sum(
            'products__orderitem__quantity',
            filter=Q(products__orderitem__order__created_at__gte=start_date)
        )
    ).order_by('-period_revenue')
    
    # Brand performance
    brand_performance = Brand.objects.annotate(
        product_count=Count('products'),
        period_revenue=Sum(
            'products__orderitem__price_at_purchase',
            filter=Q(products__orderitem__order__created_at__gte=start_date)
        ),
        period_quantity=Sum(
            'products__orderitem__quantity',
            filter=Q(products__orderitem__order__created_at__gte=start_date)
        )
    ).order_by('-period_revenue')
    
    # Price analysis
    price_ranges = [
        {'min': 0, 'max': 25, 'label': '$0 - $25'},
        {'min': 25, 'max': 50, 'label': '$25 - $50'},
        {'min': 50, 'max': 100, 'label': '$50 - $100'},
        {'min': 100, 'max': 200, 'label': '$100 - $200'},
        {'min': 200, 'max': 1000, 'label': '$200+'},
    ]
    
    price_analysis = []
    for price_range in price_ranges:
        products_in_range = Product.objects.filter(
            price__gte=price_range['min'],
            price__lt=price_range['max']
        ).count()
        
        revenue_in_range = Product.objects.filter(
            price__gte=price_range['min'],
            price__lt=price_range['max']
        ).annotate(
            period_revenue=Sum(
                'orderitem__price_at_purchase',
                filter=Q(orderitem__order__created_at__gte=start_date)
            )
        ).aggregate(
            total=Sum('period_revenue')
        )['total'] or 0
        
        price_analysis.append({
            'range': price_range['label'],
            'product_count': products_in_range,
            'revenue': revenue_in_range
        })
    
    # Stock analysis
    stock_analysis = {
        'well_stocked': Product.objects.filter(stock_quantity__gt=F('reorder_threshold') * 2).count(),
        'adequately_stocked': Product.objects.filter(
            stock_quantity__gt=F('reorder_threshold'),
            stock_quantity__lte=F('reorder_threshold') * 2
        ).count(),
        'low_stock': Product.objects.filter(
            stock_quantity__gt=0,
            stock_quantity__lte=F('reorder_threshold')
        ).count(),
        'out_of_stock': Product.objects.filter(stock_quantity=0).count(),
    }
    
    context = {
        'period': period,
        'period_days': period_days,
        'start_date': start_date,
        
        # KPIs
        'total_products': total_products,
        'active_products': active_products,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'total_sales_revenue': total_sales_revenue,
        'total_units_sold': total_units_sold,
        'average_order_value': (total_sales_revenue / total_units_sold) if total_units_sold > 0 else 0,
        
        # Performance data
        'top_products_revenue': top_products_revenue,
        'top_products_quantity': top_products_quantity,
        'bottom_products_revenue': bottom_products_revenue,
        'category_performance': category_performance,
        'brand_performance': brand_performance,
        'price_analysis': price_analysis,
        'stock_analysis': stock_analysis,
    }
    
    return render(request, 'admin_panel/product_performance_dashboard.html', context)

@admin_required
@role_required(['Admin', 'Merchandiser'])
def price_history(request):
    """View price history for all products"""
    products = Product.objects.select_related('category', 'brand').all()
    
    # Filters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    brand_filter = request.GET.get('brand', '')
    sort_by = request.GET.get('sort', 'name')
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query)
        )
    
    if category_filter:
        products = products.filter(category_id=category_filter)
    
    if brand_filter:
        products = products.filter(brand_id=brand_filter)
    
    # Sorting
    if sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'price':
        products = products.order_by('price')
    elif sort_by == 'discount_price':
        products = products.order_by('discount_price')
    elif sort_by == 'category':
        products = products.order_by('category__name')
    elif sort_by == 'brand':
        products = products.order_by('brand__name')
    
    # Pagination
    paginator = Paginator(products, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': Category.objects.filter(is_active=True),
        'brands': Brand.objects.filter(is_active=True),
        'search_query': search_query,
        'category_filter': category_filter,
        'brand_filter': brand_filter,
        'sort_by': sort_by,
    }
    
    return render(request, 'admin_panel/price_history.html', context)

@admin_required
@role_required(['Admin', 'Merchandiser'])
def price_change(request, product_id):
    """Change product price with history tracking"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        try:
            old_price = product.price
            old_discount_price = product.discount_price
            
            new_price = request.POST.get('price')
            new_discount_price = request.POST.get('discount_price') or None
            reason = request.POST.get('reason', '')
            
            if not new_price:
                messages.error(request, 'Price is required.')
                return redirect('admin_panel:price_change', product_id=product_id)
            
            new_price = float(new_price)
            if new_discount_price:
                new_discount_price = float(new_discount_price)
            
            # Update product prices
            product.price = new_price
            product.discount_price = new_discount_price
            product.save()
            
            # Log the price change
            AuditLog.objects.create(
                user=request.user,
                action='PRICE_CHANGE',
                description=f'Changed price for {product.name}',
                old_values={
                    'price': float(old_price),
                    'discount_price': float(old_discount_price) if old_discount_price else None,
                },
                new_values={
                    'price': new_price,
                    'discount_price': new_discount_price,
                    'reason': reason,
                },
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'Price updated successfully for {product.name}.')
            return redirect('admin_panel:price_history')
            
        except ValueError:
            messages.error(request, 'Invalid price format.')
        except Exception as e:
            messages.error(request, f'Error updating price: {str(e)}')
    
    context = {
        'product': product,
    }
    
    return render(request, 'admin_panel/price_change.html', context)
