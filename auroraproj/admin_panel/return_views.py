from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import transaction

from admin_panel.decorators import admin_required, role_required
from online_store.checkout.models import Order, OrderReturn, CustomerNotification
from admin_panel.models import AuditLog

@admin_required
@role_required(['superadmin', 'crm'])
def return_management(request):
    """Admin view for managing return requests"""
    returns = OrderReturn.objects.all().select_related('order', 'order__user').order_by('-requested_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        returns = returns.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(returns, 20)
    page = request.GET.get('page')
    returns_page = paginator.get_page(page)
    
    context = {
        'returns': returns_page,
        'status_filter': status_filter,
        'status_choices': OrderReturn.RETURN_STATUS_CHOICES,
    }
    
    return render(request, 'admin_panel/return_management.html', context)

@admin_required
@role_required(['superadmin', 'crm'])
def return_detail(request, return_id):
    """Admin view for detailed return request"""
    return_request = get_object_or_404(OrderReturn, id=return_id)
    
    context = {
        'return_request': return_request,
    }
    
    return render(request, 'admin_panel/return_detail.html', context)

@admin_required
@role_required(['superadmin', 'crm'])
@require_POST
def approve_return(request, return_id):
    """Approve a return request"""
    return_request = get_object_or_404(OrderReturn, id=return_id)
    
    if not return_request.can_be_approved:
        messages.error(request, 'This return request cannot be approved.')
        return redirect('admin_panel:return_detail', return_id=return_id)
    
    try:
        with transaction.atomic():
            return_request.status = 'approved'
            return_request.approved_at = timezone.now()
            return_request.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='RETURN_APPROVED',
                description=f'Approved return request for Order #{return_request.order.order_number}',
                new_values={
                    'return_id': return_request.id,
                    'order_id': return_request.order.order_id,
                    'reason': return_request.reason,
                }
            )
            
            # Send notification to customer
            CustomerNotification.create_notification(
                user=return_request.order.user,
                notification_type='return_approved',
                title='Return Request Approved',
                message=f'Your return request for Order #{return_request.order.order_number} has been approved. Please send the items back to us.',
                order=return_request.order,
                return_request=return_request
            )
            
            messages.success(request, f'Return request for Order #{return_request.order.order_number} has been approved.')
            
    except Exception as e:
        messages.error(request, f'Error approving return request: {str(e)}')
    
    return redirect('admin_panel:return_detail', return_id=return_id)

@admin_required
@role_required(['superadmin', 'crm'])
@require_POST
def reject_return(request, return_id):
    """Reject a return request"""
    return_request = get_object_or_404(OrderReturn, id=return_id)
    
    if not return_request.can_be_approved:
        messages.error(request, 'This return request cannot be rejected.')
        return redirect('admin_panel:return_detail', return_id=return_id)
    
    admin_notes = request.POST.get('admin_notes', '')
    
    try:
        with transaction.atomic():
            return_request.status = 'rejected'
            return_request.admin_notes = admin_notes
            return_request.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='RETURN_REJECTED',
                description=f'Rejected return request for Order #{return_request.order.order_number}',
                new_values={
                    'return_id': return_request.id,
                    'order_id': return_request.order.order_id,
                    'reason': return_request.reason,
                    'admin_notes': admin_notes,
                }
            )
            
            # Send notification to customer
            CustomerNotification.create_notification(
                user=return_request.order.user,
                notification_type='return_rejected',
                title='Return Request Rejected',
                message=f'Your return request for Order #{return_request.order.order_number} has been rejected. Reason: {admin_notes}',
                order=return_request.order,
                return_request=return_request
            )
            
            messages.success(request, f'Return request for Order #{return_request.order.order_number} has been rejected.')
            
    except Exception as e:
        messages.error(request, f'Error rejecting return request: {str(e)}')
    
    return redirect('admin_panel:return_detail', return_id=return_id)

@admin_required
@role_required(['superadmin', 'crm'])
@require_POST
def mark_return_received(request, return_id):
    """Mark return as received"""
    return_request = get_object_or_404(OrderReturn, id=return_id)
    
    if not return_request.can_be_received:
        messages.error(request, 'This return cannot be marked as received.')
        return redirect('admin_panel:return_detail', return_id=return_id)
    
    try:
        with transaction.atomic():
            return_request.status = 'received'
            return_request.received_at = timezone.now()
            return_request.save()
            
            # Restore product stock
            for order_item in return_request.order.order_items.all():
                order_item.product.stock_quantity += order_item.quantity
                order_item.product.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='RETURN_RECEIVED',
                description=f'Marked return as received for Order #{return_request.order.order_number}',
                new_values={
                    'return_id': return_request.id,
                    'order_id': return_request.order.order_id,
                    'items_restored': return_request.order.order_items.count(),
                }
            )
            
            # Send notification to customer
            CustomerNotification.create_notification(
                user=return_request.order.user,
                notification_type='return_received',
                title='Return Received',
                message=f'We have received your returned items for Order #{return_request.order.order_number}. Your refund will be processed shortly.',
                order=return_request.order,
                return_request=return_request
            )
            
            messages.success(request, f'Return for Order #{return_request.order.order_number} has been marked as received and stock restored.')
            
    except Exception as e:
        messages.error(request, f'Error marking return as received: {str(e)}')
    
    return redirect('admin_panel:return_detail', return_id=return_id)

@admin_required
@role_required(['superadmin', 'crm'])
@require_POST
def mark_return_shipped(request, return_id):
    """Mark return as shipped back by customer"""
    return_request = get_object_or_404(OrderReturn, id=return_id)
    
    if not return_request.can_be_shipped:
        messages.error(request, 'This return cannot be marked as shipped.')
        return redirect('admin_panel:return_detail', return_id=return_id)
    
    try:
        with transaction.atomic():
            return_request.status = 'shipped'
            return_request.shipped_at = timezone.now()
            return_request.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='RETURN_SHIPPED',
                description=f'Marked return as shipped for Order #{return_request.order.order_number}',
                new_values={
                    'return_id': return_request.id,
                    'order_id': return_request.order.order_id,
                }
            )
            
            # Send notification to customer
            CustomerNotification.create_notification(
                user=return_request.order.user,
                notification_type='return_shipped',
                title='Return Shipped',
                message=f'Your return for Order #{return_request.order.order_number} has been marked as shipped. We will notify you once we receive the items.',
                order=return_request.order,
                return_request=return_request
            )
            
            messages.success(request, f'Return for Order #{return_request.order.order_number} has been marked as shipped.')
            
    except Exception as e:
        messages.error(request, f'Error marking return as shipped: {str(e)}')
    
    return redirect('admin_panel:return_detail', return_id=return_id)

@admin_required
@role_required(['superadmin', 'crm'])
@require_POST
def process_refund(request, return_id):
    """Process refund for received return"""
    return_request = get_object_or_404(OrderReturn, id=return_id)
    
    if not return_request.can_be_refunded:
        messages.error(request, 'This return cannot be refunded.')
        return redirect('admin_panel:return_detail', return_id=return_id)
    
    try:
        with transaction.atomic():
            return_request.status = 'refunded'
            return_request.refunded_at = timezone.now()
            return_request.save()
            
            # Update order payment status
            return_request.order.payment_status = 'refunded'
            return_request.order.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='REFUND_PROCESSED',
                description=f'Processed refund for Order #{return_request.order.order_number}',
                new_values={
                    'return_id': return_request.id,
                    'order_id': return_request.order.order_id,
                    'refund_amount': float(return_request.order.total_amount),
                }
            )
            
            # Send notification to customer
            CustomerNotification.create_notification(
                user=return_request.order.user,
                notification_type='refund_processed',
                title='Refund Processed',
                message=f'Your refund of ${return_request.order.total_amount} for Order #{return_request.order.order_number} has been processed and will appear in your account within 3-5 business days.',
                order=return_request.order,
                return_request=return_request
            )
            
            messages.success(request, f'Refund processed for Order #{return_request.order.order_number}.')
            
    except Exception as e:
        messages.error(request, f'Error processing refund: {str(e)}')
    
    return redirect('admin_panel:return_detail', return_id=return_id)

@admin_required
@role_required(['superadmin', 'crm'])
@require_POST
def close_return(request, return_id):
    """Close the return process"""
    return_request = get_object_or_404(OrderReturn, id=return_id)
    
    if not return_request.can_be_closed:
        messages.error(request, 'This return cannot be closed.')
        return redirect('admin_panel:return_detail', return_id=return_id)
    
    try:
        with transaction.atomic():
            return_request.status = 'closed'
            return_request.closed_at = timezone.now()
            return_request.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='RETURN_CLOSED',
                description=f'Closed return process for Order #{return_request.order.order_number}',
                new_values={
                    'return_id': return_request.id,
                    'order_id': return_request.order.order_id,
                }
            )
            
            # Send notification to customer
            CustomerNotification.create_notification(
                user=return_request.order.user,
                notification_type='return_closed',
                title='Return Process Complete',
                message=f'Your return process for Order #{return_request.order.order_number} has been completed successfully. Thank you for your business!',
                order=return_request.order,
                return_request=return_request
            )
            
            messages.success(request, f'Return process for Order #{return_request.order.order_number} has been closed.')
            
    except Exception as e:
        messages.error(request, f'Error closing return: {str(e)}')
    
    return redirect('admin_panel:return_detail', return_id=return_id)
