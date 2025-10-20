from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from item.models import Product, Category
from profiles.models import Profile
from core.ml_service import ml_service

class Command(BaseCommand):
    help = 'Test ML service integration'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing ML Service Integration...'))
        
        # Test model loading
        status = ml_service.get_model_status()
        self.stdout.write(f"Decision Tree Model Loaded: {status['decision_tree_loaded']}")
        self.stdout.write(f"Association Rules Model Loaded: {status['association_rules_loaded']}")
        self.stdout.write(f"Feature Columns Count: {status['feature_columns_count']}")
        
        # Test category prediction
        test_user_data = {
            'age': 28,
            'household_size': 2,
            'has_children': False,
            'monthly_income_sgd': 6000,
            'gender': 'Female',
            'employment_status': 'Full-time',
            'occupation': 'Tech',
            'education': 'Bachelor'
        }
        
        predicted_category = ml_service.predict_preferred_category(test_user_data)
        self.stdout.write(f"Predicted Category: {predicted_category}")
        
        # Test product recommendations
        products = Product.objects.filter(is_active=True)[:5]
        if products:
            test_skus = [p.sku for p in products[:2]]
            recommendations = ml_service.get_product_recommendations(test_skus, top_n=3)
            self.stdout.write(f"Product Recommendations: {recommendations}")
            
            # Test frequently bought together
            fbt = ml_service.get_frequently_bought_together(test_skus[0], top_n=2)
            self.stdout.write(f"Frequently Bought Together: {fbt}")
        
        self.stdout.write(self.style.SUCCESS('ML Service Integration Test Complete!'))
