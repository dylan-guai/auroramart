from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import date
from django.db import models

from .models import BusinessMetrics, CustomerAnalytics, ProductAnalytics, MarketingAnalytics, AIPerformanceMetrics
from online_store.checkout.models import Order, OrderItem
from online_store.profiles.models import Profile
from online_store.item.models import Product, Category, ProductReview
from online_store.loyalty.models import LoyaltyAccount, LoyaltyTransaction


@receiver(post_save, sender=Order)
def update_business_metrics(sender, instance, created, **kwargs):
    """Update business metrics when orders are created or updated"""
    if instance.status == 'delivered':
        today = date.today()
        metrics, created = BusinessMetrics.objects.get_or_create(date=today)
        
        if created:
            # Initialize with current data
            metrics.total_revenue = instance.total_amount
            metrics.total_orders = 1
            metrics.completed_orders = 1
            metrics.average_order_value = instance.total_amount
        else:
            # Update existing metrics
            metrics.total_revenue += instance.total_amount
            metrics.total_orders += 1
            metrics.completed_orders += 1
            
            # Recalculate average order value
            completed_orders = Order.objects.filter(
                created_at__date=today,
                status='delivered'
            )
            metrics.average_order_value = completed_orders.aggregate(
                avg=models.Avg('total_amount')
            )['avg'] or 0
        
        metrics.save()


@receiver(post_save, sender=Profile)
def update_customer_metrics(sender, instance, created, **kwargs):
    """Update customer metrics when profiles are created"""
    if created:
        today = date.today()
        metrics, created = BusinessMetrics.objects.get_or_create(date=today)
        
        if created:
            metrics.new_customers = 1
            metrics.total_customers = 1
        else:
            metrics.new_customers += 1
            metrics.total_customers = Profile.objects.count()
        
        metrics.save()


@receiver(post_save, sender=OrderItem)
def update_product_metrics(sender, instance, created, **kwargs):
    """Update product metrics when order items are created"""
    if created and instance.order.status == 'delivered':
        today = date.today()
        metrics, created = ProductAnalytics.objects.get_or_create(date=today)
        
        if created:
            metrics.total_products_sold = instance.quantity
            metrics.unique_products_sold = 1
        else:
            metrics.total_products_sold += instance.quantity
            # Count unique products sold today
            unique_products = OrderItem.objects.filter(
                order__created_at__date=today,
                order__status='delivered'
            ).values('product').distinct().count()
            metrics.unique_products_sold = unique_products
        
        metrics.save()


@receiver(post_save, sender=LoyaltyTransaction)
def update_loyalty_metrics(sender, instance, created, **kwargs):
    """Update loyalty metrics when transactions are created"""
    if created:
        today = date.today()
        metrics, created = BusinessMetrics.objects.get_or_create(date=today)
        
        if instance.transaction_type == 'earned':
            if created:
                metrics.loyalty_points_earned = instance.points
            else:
                metrics.loyalty_points_earned += instance.points
        elif instance.transaction_type == 'redeemed':
            if created:
                metrics.loyalty_points_redeemed = abs(instance.points)
                metrics.loyalty_redemptions = 1
            else:
                metrics.loyalty_points_redeemed += abs(instance.points)
                metrics.loyalty_redemptions += 1
        
        metrics.save()


@receiver(post_save, sender=ProductReview)
def update_review_metrics(sender, instance, created, **kwargs):
    """Update review metrics when reviews are created"""
    if created:
        today = date.today()
        metrics, created = ProductAnalytics.objects.get_or_create(date=today)
        
        if created:
            metrics.total_reviews = 1
            metrics.products_with_reviews = 1
            metrics.average_rating = instance.rating
        else:
            metrics.total_reviews += 1
            # Count unique products with reviews
            products_with_reviews = ProductReview.objects.filter(
                created_at__date=today
            ).values('product').distinct().count()
            metrics.products_with_reviews = products_with_reviews
            
            # Recalculate average rating
            avg_rating = ProductReview.objects.filter(
                created_at__date=today
            ).aggregate(avg=models.Avg('rating'))['avg'] or 0
            metrics.average_rating = avg_rating
        
        metrics.save()
