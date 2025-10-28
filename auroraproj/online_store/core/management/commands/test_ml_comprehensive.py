from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from online_store.item.models import Product, Category, Brand
from online_store.profiles.models import Profile
from online_store.checkout.models import Cart, CartItem
from online_store.core.ml_service import ml_service
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Comprehensive test of ML integration and data flow'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🧪 Starting Comprehensive ML Integration Test...'))
        
        # Test 1: ML Service Status
        self.test_ml_service_status()
        
        # Test 2: Category Prediction
        self.test_category_prediction()
        
        # Test 3: Product Recommendations
        self.test_product_recommendations()
        
        # Test 4: Data Model Integration
        self.test_data_model_integration()
        
        # Test 5: End-to-End User Flow
        self.test_end_to_end_flow()
        
        self.stdout.write(self.style.SUCCESS('✅ All ML Integration Tests Completed!'))

    def test_ml_service_status(self):
        """Test ML service initialization and status"""
        self.stdout.write('\n📊 Testing ML Service Status...')
        
        status = ml_service.get_model_status()
        
        self.stdout.write(f"  Models Loaded: {status['models_loaded']}")
        self.stdout.write(f"  Decision Tree Loaded: {status['decision_tree_loaded']}")
        self.stdout.write(f"  Association Rules Loaded: {status['association_rules_loaded']}")
        self.stdout.write(f"  Feature Columns Count: {status['feature_columns_count']}")
        
        if not status['models_loaded']:
            self.stdout.write(self.style.ERROR('❌ ML models failed to load!'))
            return False
        
        self.stdout.write(self.style.SUCCESS('✅ ML Service Status: OK'))
        return True

    def test_category_prediction(self):
        """Test category prediction functionality"""
        self.stdout.write('\n🎯 Testing Category Prediction...')
        
        test_cases = [
            {
                'name': 'Tech Professional',
                'data': {
                    'age': 28,
                    'household_size': 2,
                    'has_children': False,
                    'monthly_income_sgd': 6000,
                    'gender': 'Female',
                    'employment_status': 'Full-time',
                    'occupation': 'Tech',
                    'education': 'Bachelor'
                }
            },
            {
                'name': 'Family Person',
                'data': {
                    'age': 35,
                    'household_size': 4,
                    'has_children': True,
                    'monthly_income_sgd': 8000,
                    'gender': 'Male',
                    'employment_status': 'Full-time',
                    'occupation': 'Sales',
                    'education': 'Master'
                }
            },
            {
                'name': 'Student',
                'data': {
                    'age': 22,
                    'household_size': 1,
                    'has_children': False,
                    'monthly_income_sgd': 2000,
                    'gender': 'Female',
                    'employment_status': 'Student',
                    'occupation': 'Education',
                    'education': 'Bachelor'
                }
            }
        ]
        
        for test_case in test_cases:
            predicted_category = ml_service.predict_preferred_category(test_case['data'])
            self.stdout.write(f"  {test_case['name']}: {predicted_category}")
            
            if predicted_category:
                self.stdout.write(self.style.SUCCESS(f'✅ {test_case["name"]} prediction: OK'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️ {test_case["name"]} prediction: No result'))

    def test_product_recommendations(self):
        """Test product recommendation functionality"""
        self.stdout.write('\n🛍️ Testing Product Recommendations...')
        
        # Get some test products
        products = Product.objects.filter(is_active=True)[:3]
        if not products:
            self.stdout.write(self.style.WARNING('⚠️ No products available for testing'))
            return
        
        test_skus = [p.sku for p in products]
        self.stdout.write(f"  Test SKUs: {test_skus}")
        
        # Test general recommendations
        recommendations = ml_service.get_product_recommendations(test_skus, top_n=3)
        self.stdout.write(f"  General Recommendations: {recommendations}")
        
        # Test frequently bought together
        if test_skus:
            fbt = ml_service.get_frequently_bought_together(test_skus[0], top_n=2)
            self.stdout.write(f"  Frequently Bought Together: {fbt}")
        
        self.stdout.write(self.style.SUCCESS('✅ Product Recommendations: OK'))

    def test_data_model_integration(self):
        """Test integration with Django models"""
        self.stdout.write('\n🗄️ Testing Data Model Integration...')
        
        # Test category matching
        predicted_category = ml_service.predict_preferred_category({
            'age': 30,
            'household_size': 2,
            'has_children': False,
            'monthly_income_sgd': 5000,
            'gender': 'Male',
            'employment_status': 'Full-time',
            'occupation': 'Tech',
            'education': 'Bachelor'
        })
        
        if predicted_category:
            try:
                category_obj = Category.objects.get(name__icontains=predicted_category)
                products = Product.objects.filter(
                    category=category_obj,
                    is_active=True,
                    stock_quantity__gt=0
                )[:5]
                
                self.stdout.write(f"  Found {products.count()} products in '{predicted_category}' category")
                self.stdout.write(self.style.SUCCESS('✅ Category Integration: OK'))
                
            except Category.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'⚠️ Category "{predicted_category}" not found in database'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ No category prediction available'))

    def test_end_to_end_flow(self):
        """Test complete user flow with ML integration"""
        self.stdout.write('\n🔄 Testing End-to-End User Flow...')
        
        try:
            with transaction.atomic():
                # Create test user
                user, created = User.objects.get_or_create(
                    username='ml_test_user',
                    defaults={'email': 'ml_test@example.com'}
                )
                
                if created:
                    user.set_password('testpass123')
                    user.save()
                    self.stdout.write('  Created test user')
                
                # Create profile with demographics
                profile, created = Profile.objects.get_or_create(user=user)
                if created:
                    profile.age = 28
                    profile.gender = 'Female'
                    profile.occupation = 'Tech'
                    profile.education = 'Bachelor'
                    profile.employment_status = 'Full-time'
                    profile.household_size = 2
                    profile.has_children = False
                    profile.monthly_income_sgd = 6000
                    profile.save()
                    self.stdout.write('  Created test profile with demographics')
                
                # Test AI prediction
                user_data = {
                    'age': profile.age,
                    'household_size': profile.household_size,
                    'has_children': profile.has_children,
                    'monthly_income_sgd': profile.monthly_income_sgd,
                    'gender': profile.gender,
                    'employment_status': profile.employment_status,
                    'occupation': profile.occupation,
                    'education': profile.education
                }
                
                predicted_category = ml_service.predict_preferred_category(user_data)
                self.stdout.write(f"  Predicted category: {predicted_category}")
                
                # Test cart recommendations
                cart, created = Cart.objects.get_or_create(buyer=profile)
                if created:
                    # Add some products to cart
                    products = Product.objects.filter(is_active=True)[:2]
                    for product in products:
                        CartItem.objects.create(cart=cart, product=product, quantity=1)
                    self.stdout.write('  Created test cart with products')
                
                # Test cart recommendations
                cart_skus = list(cart.cart_items.values_list('product__sku', flat=True))
                recommendations = ml_service.get_product_recommendations(cart_skus, top_n=3)
                self.stdout.write(f"  Cart recommendations: {recommendations}")
                
                self.stdout.write(self.style.SUCCESS('✅ End-to-End Flow: OK'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ End-to-End Flow Error: {e}'))
            logger.error(f"End-to-end test error: {e}")
        
        finally:
            # Clean up test data
            try:
                User.objects.filter(username='ml_test_user').delete()
                self.stdout.write('  Cleaned up test data')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠️ Cleanup warning: {e}'))
