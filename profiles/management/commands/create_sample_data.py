from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from item.models import Product, Category, Brand
from checkout.models import Order, OrderItem, Cart, CartItem
from profiles.models import Profile, Wishlist
from decimal import Decimal
from django.utils import timezone

class Command(BaseCommand):
    help = 'Create sample data for testing'

    def handle(self, *args, **options):
        # Create a test user if it doesn't exist
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Created test user: testuser'))
        
        # Create categories and brands if they don't exist
        electronics, _ = Category.objects.get_or_create(
            name='Electronics',
            defaults={'description': 'Electronic devices and gadgets'}
        )
        
        apple, _ = Brand.objects.get_or_create(
            name='Apple',
            defaults={'description': 'Apple Inc.'}
        )
        
        # Create sample products
        products = []
        for i in range(5):
            product, created = Product.objects.get_or_create(
                name=f'Test Product {i+1}',
                defaults={
                    'slug': f'test-product-{i+1}',
                    'sku': f'TEST{i+1:03d}',
                    'description': f'This is a test product {i+1}',
                    'short_description': f'Test product {i+1}',
                    'price': Decimal('99.99'),
                    'category': electronics,
                    'brand': apple,
                    'stock_quantity': 10,
                    'is_active': True
                }
            )
            products.append(product)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created product: {product.name}'))
        
        # Create sample orders
        profile = user.profile
        for i in range(3):
            order, created = Order.objects.get_or_create(
                order_number=f'TEST{i+1:03d}',
                defaults={
                    'user': user,
                    'status': 'delivered' if i == 0 else 'processing',
                    'total_amount': Decimal('99.99'),
                    'shipping_address': '123 Test St, Singapore',
                    'shipping_name': 'Test User',
                    'shipping_city': 'Singapore',
                    'shipping_country': 'Singapore'
                }
            )
            
            if created:
                # Add order items
                OrderItem.objects.create(
                    order=order,
                    product=products[i],
                    quantity=1,
                    price_at_purchase=products[i].price
                )
                self.stdout.write(self.style.SUCCESS(f'Created order: {order.order_number}'))
        
        # Add some items to wishlist
        for product in products[:2]:
            Wishlist.objects.get_or_create(
                user=user,
                product=product
            )
        
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
        self.stdout.write('Test user: testuser / testpass123')
