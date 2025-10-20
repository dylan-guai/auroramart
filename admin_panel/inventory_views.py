from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg, F, Case, When, Value, CharField
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
import csv

from item.models import Product, Category, Subcategory
from checkout.models import Order, OrderItem
from admin_panel.decorators import admin_required, role_required
from admin_panel.models import AuditLog

@admin_required
@role_required(['Admin', 'Inventory'])
def inventory_overview(request):
    """Inventory overview with stock levels and thresholds"""
    products = Product.objects.select_related('category', 'subcategory', 'brand').all()
    
    # Filters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
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
    
    # Apply status filter
    if status_filter == 'low_stock':
        products = products.filter(stock_quantity__lte=F('reorder_threshold'))
    elif status_filter == 'out_of_stock':
        products = products.filter(stock_quantity=0)
    elif status_filter == 'in_stock':
        products = products.filter(stock_quantity__gt=F('reorder_threshold'))
    
    # Apply sorting
    if sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == '-name':
        products = products.order_by('-name')
    elif sort_by == 'stock':
        products = products.order_by('stock_quantity')
    elif sort_by == '-stock':
        products = products.order_by('-stock_quantity')
    elif sort_by == 'threshold':
        products = products.order_by('reorder_threshold')
    elif sort_by == '-threshold':
        products = products.order_by('-reorder_threshold')
    else:
        products = products.order_by('name')
    
    # Annotate with stock status
    products = products.annotate(
        stock_status=Case(
            When(stock_quantity=0, then=Value('Out of Stock')),
            When(stock_quantity__lte=F('reorder_threshold'), then=Value('Low Stock')),
            default=Value('In Stock'),
            output_field=CharField()
        )
    )
    
    # Pagination
    paginator = Paginator(products, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    categories = Category.objects.all()
    
    # Statistics
    total_products = Product.objects.count()
    low_stock_count = Product.objects.filter(stock_quantity__lte=F('reorder_threshold')).count()
    out_of_stock_count = Product.objects.filter(stock_quantity=0).count()
    total_value = Product.objects.aggregate(
        total=Sum(F('stock_quantity') * F('price'))
    )['total'] or 0
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'categories': categories,
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'total_value': total_value,
    }
    
    return render(request, 'admin_panel/inventory_overview.html', context)

@admin_required
@role_required(['Admin', 'Inventory'])
def low_stock_alerts(request):
    """Low stock alerts dashboard"""
    low_stock_products = Product.objects.filter(
        stock_quantity__lte=F('reorder_threshold')
    ).select_related('category', 'subcategory', 'brand').order_by('stock_quantity')
    
    # Group by severity
    critical_products = low_stock_products.filter(stock_quantity=0)
    warning_products = low_stock_products.filter(stock_quantity__gt=0)
    
    # Statistics
    total_low_stock = low_stock_products.count()
    critical_count = critical_products.count()
    warning_count = warning_products.count()
    
    # Estimated days of cover (simplified calculation)
    # This would ideally use historical sales data
    products_with_days = []
    for product in low_stock_products:
        # Simple estimation: assume 1 unit sold per day on average
        # In a real system, this would use actual sales velocity
        estimated_days = product.stock_quantity if product.stock_quantity > 0 else 0
        products_with_days.append({
            'product': product,
            'estimated_days': estimated_days
        })
    
    context = {
        'critical_products': critical_products,
        'warning_products': warning_products,
        'products_with_days': products_with_days,
        'total_low_stock': total_low_stock,
        'critical_count': critical_count,
        'warning_count': warning_count,
    }
    
    return render(request, 'admin_panel/low_stock_alerts.html', context)

@admin_required
@role_required(['Admin', 'Inventory'])
def stock_adjustments(request):
    """Stock adjustment history and management"""
    # Get recent adjustments (this would come from a StockAdjustment model in a real system)
    # For now, we'll show recent order activities that affected stock
    
    recent_orders = Order.objects.select_related('user').prefetch_related('order_items__product').order_by('-created_at')[:50]
    
    # Create adjustment-like entries from order data
    adjustments = []
    for order in recent_orders:
        for item in order.order_items.all():
            adjustments.append({
                'date': order.created_at,
                'product': item.product,
                'quantity_change': -item.quantity,  # Negative because it's a sale
                'reason': 'Sale',
                'order': order,
                'user': order.user,
                'reference': f'Order #{order.order_id}'
            })
    
    # Pagination
    paginator = Paginator(adjustments, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'admin_panel/stock_adjustments.html', context)

@admin_required
@role_required(['Admin', 'Inventory'])
def stock_adjustment_create(request):
    """Create a new stock adjustment"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity_change = request.POST.get('quantity_change')
        reason = request.POST.get('reason')
        notes = request.POST.get('notes', '')
        
        try:
            product = Product.objects.get(id=product_id)
            quantity_change = int(quantity_change)
            
            # Check if adjustment would result in negative stock
            new_quantity = product.stock_quantity + quantity_change
            if new_quantity < 0:
                messages.error(request, f'Cannot adjust stock below zero. Current stock: {product.stock_quantity}')
                return redirect('admin_panel:stock_adjustment_create')
            
            # Update stock
            product.stock_quantity = new_quantity
            product.save()
            
            # Log the adjustment
            AuditLog.objects.create(
                user=request.user,
                action='STOCK_ADJUSTMENT',
                description=f'Stock adjustment for {product.name}. Quantity change: {quantity_change:+d}, Reason: {reason}, Notes: {notes}'
            )
            
            messages.success(request, f'Stock adjusted successfully. New quantity: {new_quantity}')
            return redirect('admin_panel:inventory_overview')
            
        except Product.DoesNotExist:
            messages.error(request, 'Product not found')
        except ValueError:
            messages.error(request, 'Invalid quantity')
        except Exception as e:
            messages.error(request, f'Error adjusting stock: {str(e)}')
    
    # Get products for the form
    products = Product.objects.all().order_by('name')
    
    context = {
        'products': products,
    }
    
    return render(request, 'admin_panel/stock_adjustment_create.html', context)

@admin_required
@role_required(['Admin', 'Inventory'])
def receiving_management(request):
    """Receiving and restocking management"""
    # In a real system, this would manage incoming shipments
    # For now, we'll show products that need restocking
    
    products_needing_restock = Product.objects.filter(
        stock_quantity__lte=F('reorder_threshold')
    ).select_related('category', 'subcategory', 'brand').order_by('stock_quantity')
    
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        received_quantity = request.POST.get('received_quantity')
        
        try:
            product = Product.objects.get(id=product_id)
            received_quantity = int(received_quantity)
            
            # Update stock
            product.stock_quantity += received_quantity
            product.save()
            
            # Log the receiving
            AuditLog.objects.create(
                user=request.user,
                action='STOCK_RECEIVED',
                description=f'Received stock for {product.name}. Quantity received: {received_quantity}, New total: {product.stock_quantity}'
            )
            
            messages.success(request, f'Stock received successfully. New quantity: {product.stock_quantity}')
            return redirect('admin_panel:receiving_management')
            
        except Product.DoesNotExist:
            messages.error(request, 'Product not found')
        except ValueError:
            messages.error(request, 'Invalid quantity')
        except Exception as e:
            messages.error(request, f'Error receiving stock: {str(e)}')
    
    context = {
        'products_needing_restock': products_needing_restock,
    }
    
    return render(request, 'admin_panel/receiving_management.html', context)

@admin_required
@role_required(['Admin', 'Inventory'])
def reorder_suggestions(request):
    """Reorder suggestions based on sales velocity"""
    # Calculate reorder suggestions based on recent sales
    # This is a simplified version - in reality, you'd use more sophisticated algorithms
    
    products = Product.objects.annotate(
        recent_sales=Sum(
            'orderitem__quantity',
            filter=Q(orderitem__order__created_at__gte=timezone.now() - timedelta(days=14))
        )
    ).filter(recent_sales__gt=0).order_by('-reorder_threshold')
    
    suggestions = []
    for product in products:
        # Simple reorder calculation: 30 days of sales + safety stock
        daily_sales = product.recent_sales / 14  # Average daily sales over 14 days
        suggested_reorder = int(daily_sales * 30) + product.reorder_threshold
        
        suggestions.append({
            'product': product,
            'current_stock': product.stock_quantity,
            'reorder_threshold': product.reorder_threshold,
            'daily_sales': daily_sales,
            'suggested_reorder': suggested_reorder,
            'days_of_cover': product.stock_quantity / daily_sales if daily_sales > 0 else 0
        })
    
    context = {
        'suggestions': suggestions,
    }
    
    return render(request, 'admin_panel/reorder_suggestions.html', context)

@admin_required
@role_required(['Admin', 'Inventory'])
def export_inventory(request):
    """Export inventory data to CSV"""
    products = Product.objects.select_related('category', 'subcategory', 'brand').all()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'SKU', 'Name', 'Category', 'Subcategory', 'Brand', 'Current Stock',
        'Reorder Threshold', 'Price', 'Stock Status', 'Days of Cover'
    ])
    
    for product in products:
        # Calculate stock status
        if product.stock_quantity == 0:
            status = 'Out of Stock'
        elif product.stock_quantity <= product.reorder_threshold:
            status = 'Low Stock'
        else:
            status = 'In Stock'
        
        # Simple days of cover calculation (would be more sophisticated in reality)
        days_of_cover = product.stock_quantity  # Simplified
        
        writer.writerow([
            product.sku,
            product.name,
            product.category.name if product.category else '',
            product.subcategory.name if product.subcategory else '',
            product.brand.name if product.brand else '',
            product.stock_quantity,
            product.reorder_threshold,
            product.price,
            status,
            days_of_cover
        ])
    
    return response
