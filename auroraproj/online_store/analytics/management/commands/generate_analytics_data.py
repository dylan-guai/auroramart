from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import random

from online_store.analytics.models import BusinessMetrics, CustomerAnalytics, ProductAnalytics, MarketingAnalytics, AIPerformanceMetrics
from online_store.checkout.models import Order
from online_store.profiles.models import Profile
from online_store.item.models import Product, Category


class Command(BaseCommand):
    help = 'Generate sample analytics data for the past 30 days'

    def handle(self, *args, **options):
        self.stdout.write('Generating sample analytics data...')
        
        # Generate data for the past 30 days
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        current_date = start_date
        while current_date <= end_date:
            # Generate business metrics
            self.generate_business_metrics(current_date)
            
            # Generate customer analytics
            self.generate_customer_analytics(current_date)
            
            # Generate product analytics
            self.generate_product_analytics(current_date)
            
            # Generate marketing analytics
            self.generate_marketing_analytics(current_date)
            
            # Generate AI performance metrics
            self.generate_ai_metrics(current_date)
            
            current_date += timedelta(days=1)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully generated analytics data!')
        )
    
    def generate_business_metrics(self, date):
        """Generate business metrics for a specific date"""
        # Base values with some randomness
        base_revenue = random.uniform(1000, 5000)
        base_orders = random.randint(20, 100)
        base_customers = random.randint(5, 25)
        
        metrics, created = BusinessMetrics.objects.get_or_create(
            date=date,
            defaults={
                'total_revenue': Decimal(str(round(base_revenue, 2))),
                'gross_profit': Decimal(str(round(base_revenue * 0.6, 2))),
                'net_profit': Decimal(str(round(base_revenue * 0.15, 2))),
                'total_orders': base_orders,
                'completed_orders': int(base_orders * 0.85),
                'cancelled_orders': int(base_orders * 0.05),
                'average_order_value': Decimal(str(round(base_revenue / base_orders, 2))),
                'new_customers': base_customers,
                'returning_customers': int(base_customers * 0.3),
                'total_customers': Profile.objects.count(),
                'customer_retention_rate': Decimal(str(round(random.uniform(70, 90), 2))),
                'products_sold': random.randint(50, 200),
                'unique_products_sold': random.randint(20, 80),
                'top_selling_category': random.choice(['Electronics', 'Fashion', 'Home & Kitchen']),
                'page_views': random.randint(1000, 5000),
                'unique_visitors': random.randint(200, 800),
                'conversion_rate': Decimal(str(round(random.uniform(2, 8), 2))),
                'cart_abandonment_rate': Decimal(str(round(random.uniform(60, 80), 2))),
                'loyalty_points_earned': random.randint(500, 2000),
                'loyalty_points_redeemed': random.randint(100, 800),
                'loyalty_redemptions': random.randint(5, 30),
            }
        )
        
        if created:
            self.stdout.write(f'Created business metrics for {date}')
    
    def generate_customer_analytics(self, date):
        """Generate customer analytics for a specific date"""
        analytics, created = CustomerAnalytics.objects.get_or_create(
            date=date,
            defaults={
                'age_distribution': {
                    '18-25': random.randint(10, 30),
                    '26-35': random.randint(20, 50),
                    '36-45': random.randint(15, 40),
                    '46-55': random.randint(10, 25),
                    '55+': random.randint(5, 15),
                },
                'gender_distribution': {
                    'Male': random.randint(40, 60),
                    'Female': random.randint(40, 60),
                    'Other': random.randint(0, 5),
                },
                'location_distribution': {
                    'Singapore': random.randint(30, 60),
                    'Malaysia': random.randint(15, 30),
                    'Thailand': random.randint(10, 25),
                    'Indonesia': random.randint(8, 20),
                    'Philippines': random.randint(5, 15),
                },
                'average_session_duration': Decimal(str(round(random.uniform(120, 300), 2))),
                'pages_per_session': Decimal(str(round(random.uniform(3, 8), 2))),
                'bounce_rate': Decimal(str(round(random.uniform(40, 70), 2))),
                'purchase_frequency': Decimal(str(round(random.uniform(1.5, 4.0), 2))),
                'average_purchase_value': Decimal(str(round(random.uniform(50, 200), 2))),
                'customer_lifetime_value': Decimal(str(round(random.uniform(200, 800), 2))),
                'high_value_customers': random.randint(5, 20),
                'medium_value_customers': random.randint(20, 50),
                'low_value_customers': random.randint(30, 80),
            }
        )
        
        if created:
            self.stdout.write(f'Created customer analytics for {date}')
    
    def generate_product_analytics(self, date):
        """Generate product analytics for a specific date"""
        analytics, created = ProductAnalytics.objects.get_or_create(
            date=date,
            defaults={
                'total_products_sold': random.randint(100, 500),
                'revenue_by_category': {
                    'Electronics': random.randint(1000, 3000),
                    'Fashion': random.randint(800, 2500),
                    'Home & Kitchen': random.randint(600, 2000),
                    'Beauty & Personal Care': random.randint(400, 1500),
                    'Sports & Outdoors': random.randint(200, 800),
                },
                'top_selling_products': [
                    {'name': 'iPhone 15', 'units_sold': random.randint(10, 50)},
                    {'name': 'Samsung Galaxy S24', 'units_sold': random.randint(8, 40)},
                    {'name': 'MacBook Pro', 'units_sold': random.randint(5, 25)},
                ],
                'low_selling_products': [
                    {'name': 'Generic Cable', 'units_sold': random.randint(1, 5)},
                    {'name': 'Old Model Phone', 'units_sold': random.randint(0, 3)},
                ],
                'total_inventory_value': Decimal(str(round(random.uniform(50000, 200000), 2))),
                'low_stock_products': random.randint(5, 25),
                'out_of_stock_products': random.randint(0, 10),
                'inventory_turnover_rate': Decimal(str(round(random.uniform(2, 8), 2))),
                'average_rating': Decimal(str(round(random.uniform(3.5, 4.8), 2))),
                'total_reviews': random.randint(50, 200),
                'products_with_reviews': random.randint(20, 80),
                'most_searched_products': [
                    'iPhone', 'Samsung', 'MacBook', 'Nike', 'Adidas'
                ],
                'search_no_results': random.randint(50, 200),
                'search_conversion_rate': Decimal(str(round(random.uniform(5, 15), 2))),
            }
        )
        
        if created:
            self.stdout.write(f'Created product analytics for {date}')
    
    def generate_marketing_analytics(self, date):
        """Generate marketing analytics for a specific date"""
        analytics, created = MarketingAnalytics.objects.get_or_create(
            date=date,
            defaults={
                'organic_traffic': random.randint(500, 2000),
                'paid_traffic': random.randint(200, 800),
                'social_traffic': random.randint(100, 500),
                'direct_traffic': random.randint(300, 1000),
                'referral_traffic': random.randint(50, 300),
                'email_campaigns_sent': random.randint(5, 20),
                'email_open_rate': Decimal(str(round(random.uniform(15, 35), 2))),
                'email_click_rate': Decimal(str(round(random.uniform(2, 8), 2))),
                'email_conversion_rate': Decimal(str(round(random.uniform(1, 5), 2))),
                'social_media_posts': random.randint(3, 15),
                'social_media_engagement': random.randint(100, 1000),
                'social_media_reach': random.randint(500, 3000),
                'marketing_spend': Decimal(str(round(random.uniform(500, 2000), 2))),
                'marketing_revenue': Decimal(str(round(random.uniform(2000, 8000), 2))),
                'marketing_roi': Decimal(str(round(random.uniform(200, 500), 2))),
            }
        )
        
        if created:
            self.stdout.write(f'Created marketing analytics for {date}')
    
    def generate_ai_metrics(self, date):
        """Generate AI performance metrics for a specific date"""
        analytics, created = AIPerformanceMetrics.objects.get_or_create(
            date=date,
            defaults={
                'total_recommendations_shown': random.randint(500, 2000),
                'recommendations_clicked': random.randint(50, 300),
                'recommendations_converted': random.randint(10, 80),
                'recommendation_click_rate': Decimal(str(round(random.uniform(8, 20), 2))),
                'recommendation_conversion_rate': Decimal(str(round(random.uniform(5, 15), 2))),
                'personalized_content_views': random.randint(200, 800),
                'personalization_engagement_rate': Decimal(str(round(random.uniform(10, 25), 2))),
                'personalization_conversion_rate': Decimal(str(round(random.uniform(6, 18), 2))),
                'decision_tree_accuracy': Decimal(str(round(random.uniform(75, 95), 2))),
                'association_rules_confidence': Decimal(str(round(random.uniform(60, 85), 2))),
                'model_prediction_count': random.randint(1000, 5000),
                'ai_driven_revenue': Decimal(str(round(random.uniform(1000, 4000), 2))),
                'ai_driven_orders': random.randint(20, 100),
                'ai_improvement_rate': Decimal(str(round(random.uniform(5, 25), 2))),
            }
        )
        
        if created:
            self.stdout.write(f'Created AI performance metrics for {date}')
