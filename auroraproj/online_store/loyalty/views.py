from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import (
    LoyaltyTier, LoyaltyAccount, LoyaltyTransaction, 
    LoyaltyReward, LoyaltyRedemption, LoyaltyNotification
)
from online_store.checkout.models import Order
from online_store.profiles.models import Profile


@login_required
def loyalty_dashboard(request):
    """Main loyalty program dashboard for customers"""
    try:
        loyalty_account = request.user.loyalty_account
    except LoyaltyAccount.DoesNotExist:
        # Create loyalty account if it doesn't exist
        loyalty_account = LoyaltyAccount.objects.create(user=request.user)
    
    # Get recent transactions
    recent_transactions = loyalty_account.transactions.all()[:10]
    
    # Get available rewards
    available_rewards = LoyaltyReward.objects.filter(
        is_active=True,
        valid_from__lte=timezone.now(),
        valid_until__gte=timezone.now()
    ).order_by('points_cost')
    
    # Get active redemptions
    active_redemptions = loyalty_account.redemptions.filter(
        status__in=['active', 'pending']
    ).order_by('-redeemed_at')
    
    # Get unread notifications
    unread_notifications = loyalty_account.notifications.filter(is_read=False)[:5]
    
    context = {
        'loyalty_account': loyalty_account,
        'recent_transactions': recent_transactions,
        'available_rewards': available_rewards,
        'active_redemptions': active_redemptions,
        'unread_notifications': unread_notifications,
    }
    
    return render(request, 'loyalty/dashboard.html', context)


@login_required
def loyalty_rewards(request):
    """Display available rewards for redemption"""
    try:
        loyalty_account = request.user.loyalty_account
    except LoyaltyAccount.DoesNotExist:
        loyalty_account = LoyaltyAccount.objects.create(user=request.user)
    
    # Get all available rewards
    rewards = LoyaltyReward.objects.filter(
        is_active=True,
        valid_from__lte=timezone.now(),
        valid_until__gte=timezone.now()
    ).order_by('points_cost')
    
    # Filter by tier if applicable
    if loyalty_account.current_tier:
        rewards = rewards.filter(
            points_cost__lte=loyalty_account.points_balance
        )
    
    context = {
        'loyalty_account': loyalty_account,
        'rewards': rewards,
    }
    
    return render(request, 'loyalty/rewards.html', context)


@login_required
def redeem_reward(request, reward_id):
    """Redeem a loyalty reward"""
    reward = get_object_or_404(LoyaltyReward, id=reward_id, is_active=True)
    
    try:
        loyalty_account = request.user.loyalty_account
    except LoyaltyAccount.DoesNotExist:
        loyalty_account = LoyaltyAccount.objects.create(user=request.user)
    
    # Check if user has enough points
    if loyalty_account.points_balance < reward.points_cost:
        messages.error(request, 'Insufficient points to redeem this reward.')
        return redirect('loyalty:rewards')
    
    # Check if reward is available
    if not reward.is_available:
        messages.error(request, 'This reward is no longer available.')
        return redirect('loyalty:rewards')
    
    # Check if user has already redeemed this reward recently
    recent_redemption = loyalty_account.redemptions.filter(
        reward=reward,
        status__in=['active', 'pending'],
        redeemed_at__gte=timezone.now() - timedelta(days=30)
    ).exists()
    
    if recent_redemption:
        messages.error(request, 'You have already redeemed this reward recently.')
        return redirect('loyalty:rewards')
    
    try:
        # Create redemption
        redemption = LoyaltyRedemption.objects.create(
            account=loyalty_account,
            reward=reward,
            points_used=reward.points_cost,
            expires_at=timezone.now() + timedelta(days=30)
        )
        
        # Deduct points
        loyalty_account.redeem_points(
            reward.points_cost,
            f'Redeemed reward: {reward.name}'
        )
        
        # Update reward redemption count
        reward.current_redemptions += 1
        reward.save()
        
        # Create notification
        LoyaltyNotification.objects.create(
            account=loyalty_account,
            notification_type='reward_redeemed',
            title='Reward Redeemed Successfully!',
            message=f'You have successfully redeemed {reward.name}. Your reward is valid for 30 days.',
            is_read=False
        )
        
        messages.success(request, f'Successfully redeemed {reward.name}!')
        
    except Exception as e:
        messages.error(request, f'Error redeeming reward: {str(e)}')
    
    return redirect('loyalty:dashboard')


@login_required
def loyalty_transactions(request):
    """Display loyalty point transaction history"""
    try:
        loyalty_account = request.user.loyalty_account
    except LoyaltyAccount.DoesNotExist:
        loyalty_account = LoyaltyAccount.objects.create(user=request.user)
    
    # Get all transactions with pagination
    transactions = loyalty_account.transactions.all()
    
    # Filter by date range if provided
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        transactions = transactions.filter(created_at__date__gte=start_date)
    if end_date:
        transactions = transactions.filter(created_at__date__lte=end_date)
    
    # Filter by transaction type
    transaction_type = request.GET.get('type')
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    transactions = transactions.order_by('-created_at')
    
    context = {
        'loyalty_account': loyalty_account,
        'transactions': transactions,
        'start_date': start_date,
        'end_date': end_date,
        'transaction_type': transaction_type,
    }
    
    return render(request, 'loyalty/transactions.html', context)


@login_required
def loyalty_notifications(request):
    """Display loyalty notifications"""
    try:
        loyalty_account = request.user.loyalty_account
    except LoyaltyAccount.DoesNotExist:
        loyalty_account = LoyaltyAccount.objects.create(user=request.user)
    
    notifications = loyalty_account.notifications.all().order_by('-created_at')
    
    # Mark all notifications as read
    loyalty_account.notifications.filter(is_read=False).update(is_read=True)
    
    context = {
        'loyalty_account': loyalty_account,
        'notifications': notifications,
    }
    
    return render(request, 'loyalty/notifications.html', context)


@login_required
def loyalty_tiers(request):
    """Display loyalty tier information and benefits"""
    tiers = LoyaltyTier.objects.filter(is_active=True).order_by('min_points')
    
    try:
        loyalty_account = request.user.loyalty_account
    except LoyaltyAccount.DoesNotExist:
        loyalty_account = LoyaltyAccount.objects.create(user=request.user)
    
    context = {
        'tiers': tiers,
        'loyalty_account': loyalty_account,
    }
    
    return render(request, 'loyalty/tiers.html', context)


def loyalty_api_points(request):
    """API endpoint to get user's loyalty points"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        loyalty_account = request.user.loyalty_account
        return JsonResponse({
            'points_balance': loyalty_account.points_balance,
            'lifetime_points': loyalty_account.lifetime_points,
            'current_tier': loyalty_account.current_tier.display_name if loyalty_account.current_tier else 'No Tier',
            'points_to_next_tier': loyalty_account.points_to_next_tier,
            'tier_progress': loyalty_account.tier_progress_percentage,
        })
    except LoyaltyAccount.DoesNotExist:
        return JsonResponse({
            'points_balance': 0,
            'lifetime_points': 0,
            'current_tier': 'No Tier',
            'points_to_next_tier': 0,
            'tier_progress': 0,
        })


def loyalty_api_tier_info(request):
    """API endpoint to get tier information"""
    tiers = LoyaltyTier.objects.filter(is_active=True).order_by('min_points')
    tier_data = []
    
    for tier in tiers:
        tier_data.append({
            'name': tier.name,
            'display_name': tier.display_name,
            'min_points': tier.min_points,
            'point_multiplier': float(tier.point_multiplier),
            'discount_percentage': float(tier.discount_percentage),
            'free_shipping': tier.free_shipping,
            'priority_support': tier.priority_support,
            'exclusive_access': tier.exclusive_access,
            'color': tier.color,
            'icon': tier.icon,
            'description': tier.description,
        })
    
    return JsonResponse({'tiers': tier_data})
