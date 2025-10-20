from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from .models import LoyaltyAccount, LoyaltyTransaction, LoyaltyNotification
from checkout.models import Order, OrderItem
from item.models import ProductReview


@receiver(post_save, sender=User)
def create_loyalty_account(sender, instance, created, **kwargs):
    """Create loyalty account when user is created"""
    if created:
        LoyaltyAccount.objects.get_or_create(user=instance)


@receiver(post_save, sender=Order)
def award_purchase_points(sender, instance, created, **kwargs):
    """Award loyalty points when order is completed"""
    if instance.status == 'delivered' and not created:
        try:
            loyalty_account = instance.user.loyalty_account
        except LoyaltyAccount.DoesNotExist:
            loyalty_account = LoyaltyAccount.objects.create(user=instance.user)
        
        # Award points based on order value (1 point per $1)
        points = int(instance.total_amount)
        
        if points > 0:
            loyalty_account.add_points(
                points,
                source='purchase',
                description=f'Purchase points for order #{instance.order_number}'
            )
            
            # Create notification
            LoyaltyNotification.objects.create(
                account=loyalty_account,
                notification_type='points_earned',
                title='Points Earned!',
                message=f'You earned {points} points for your purchase of ${instance.total_amount}.',
                is_read=False
            )


@receiver(post_save, sender=ProductReview)
def award_review_points(sender, instance, created, **kwargs):
    """Award loyalty points for product reviews"""
    if created and instance.rating >= 4:  # Only award points for good reviews
        try:
            loyalty_account = instance.user.loyalty_account
        except LoyaltyAccount.DoesNotExist:
            loyalty_account = LoyaltyAccount.objects.create(user=instance.user)
        
        # Award 10 points for reviews
        points = 10
        
        loyalty_account.add_points(
            points,
            source='review',
            description=f'Review points for {instance.product.name}'
        )
        
        # Create notification
        LoyaltyNotification.objects.create(
            account=loyalty_account,
            notification_type='points_earned',
            title='Review Points Earned!',
            message=f'You earned {points} points for reviewing {instance.product.name}.',
            is_read=False
        )


@receiver(post_save, sender=User)
def award_birthday_points(sender, instance, created, **kwargs):
    """Award birthday points (placeholder - would need birthday field)"""
    # This would require adding a birthday field to the Profile model
    # For now, it's a placeholder for future implementation
    pass
