from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.conf import settings
import requests
import os
from PIL import Image
import io
from online_store.item.models import Product, Category, Subcategory, Brand, ProductImage
from online_store.profiles.models import Profile
import random

class Command(BaseCommand):
    help = 'Add realistic images for products, categories, and profile photos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--category-images',
            action='store_true',
            help='Add images for categories',
        )
        parser.add_argument(
            '--product-images',
            action='store_true',
            help='Add images for products',
        )
        parser.add_argument(
            '--profile-images',
            action='store_true',
            help='Add profile photos for users',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Add all types of images',
        )

    def handle(self, *args, **options):
        if options['all']:
            self.add_category_images()
            self.add_product_images()
            self.add_profile_images()
        else:
            if options['category_images']:
                self.add_category_images()
            if options['product_images']:
                self.add_product_images()
            if options['profile_images']:
                self.add_profile_images()

    def add_category_images(self):
        """Add images for categories"""
        self.stdout.write('Adding category images...')
        
        category_images = {
            'Electronics': [
                'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1518717758536-85ae29035b6d?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=400&h=300&fit=crop'
            ],
            'Fashion': [
                'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1445205170230-053b83016050?w=400&h=300&fit=crop'
            ],
            'Home & Kitchen': [
                'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=300&fit=crop'
            ],
            'Beauty & Personal Care': [
                'https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=400&h=300&fit=crop'
            ],
            'Sports & Outdoors': [
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=300&fit=crop'
            ],
            'Books': [
                'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400&h=300&fit=crop'
            ],
            'Groceries & Gourmet': [
                'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=300&fit=crop'
            ],
            'Health & Wellness': [
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=300&fit=crop'
            ],
            'Automotive': [
                'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1562141961-8b8b0b8b8b8b?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop'
            ]
        }

        for category_name, image_urls in category_images.items():
            try:
                category = Category.objects.get(name=category_name)
                if not category.image:
                    image_url = random.choice(image_urls)
                    image_data = self.download_image(image_url)
                    if image_data:
                        category.image.save(
                            f'{category.slug}_category.jpg',
                            ContentFile(image_data),
                            save=True
                        )
                        self.stdout.write(f'  ✓ Added image for {category.name}')
                    else:
                        self.stdout.write(f'  ✗ Failed to download image for {category.name}')
                else:
                    self.stdout.write(f'  - {category.name} already has an image')
            except Category.DoesNotExist:
                self.stdout.write(f'  ✗ Category {category_name} not found')

    def add_product_images(self):
        """Add images for products"""
        self.stdout.write('Adding product images...')
        
        # Specific product image mappings
        product_specific_images = {
            # Electronics
            'Apple Watch': [
                'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=500&h=500&fit=crop'
            ],
            'iPhone': [
                'https://images.unsplash.com/photo-1592899677977-9e10b8442d0b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1592899677977-9e10b8442d0b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1592899677977-9e10b8442d0b?w=500&h=500&fit=crop'
            ],
            'Samsung Galaxy': [
                'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500&h=500&fit=crop'
            ],
            'MacBook': [
                'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500&h=500&fit=crop'
            ],
            'PlayStation': [
                'https://images.unsplash.com/photo-1606144042614-b2417e99c4e3?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1606144042614-b2417e99c4e3?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1606144042614-b2417e99c4e3?w=500&h=500&fit=crop'
            ],
            'Canon EOS': [
                'https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=500&h=500&fit=crop'
            ],
            'Sony WH': [
                'https://images.unsplash.com/photo-1583394838336-acd977736f90?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1583394838336-acd977736f90?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1583394838336-acd977736f90?w=500&h=500&fit=crop'
            ],
            
            # Fashion
            'North Face Jacket': [
                'https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=500&h=500&fit=crop'
            ],
            'Ray-Ban': [
                'https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=500&h=500&fit=crop'
            ],
            'Gucci Handbag': [
                'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&h=500&fit=crop'
            ],
            'Chanel No. 5': [
                'https://images.unsplash.com/photo-1541643600914-78b084683601?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1541643600914-78b084683601?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1541643600914-78b084683601?w=500&h=500&fit=crop'
            ],
            'Rolex Submariner': [
                'https://images.unsplash.com/photo-1523170335258-f5e6a7c0c1c1?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1523170335258-f5e6a7c0c1c1?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1523170335258-f5e6a7c0c1c1?w=500&h=500&fit=crop'
            ],
            'Levi\'s 501 Jeans': [
                'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=500&h=500&fit=crop'
            ],
            'Zara Blazer': [
                'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=500&h=500&fit=crop'
            ],
            'Uniqlo Heattech T-Shirt': [
                'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=500&h=500&fit=crop'
            ],
            'Adidas Ultraboost': [
                'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&h=500&fit=crop'
            ],
            'Nike Air Max': [
                'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=500&h=500&fit=crop'
            ],
            
            # Home & Kitchen
            'Roomba': [
                'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500&h=500&fit=crop'
            ],
            'Tempur-Pedic Pillow': [
                'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=500&h=500&fit=crop'
            ],
            'Vitamix Blender': [
                'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=500&h=500&fit=crop'
            ],
            'Nespresso Machine': [
                'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=500&h=500&fit=crop'
            ],
            'Philips Hue Bulbs': [
                'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500&h=500&fit=crop'
            ],
            'Le Creuset Dutch Oven': [
                'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=500&h=500&fit=crop'
            ],
            'Instant Pot Duo': [
                'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=500&h=500&fit=crop'
            ],
            'IKEA Dining Table': [
                'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=500&h=500&fit=crop'
            ],
            'Dyson V15 Vacuum': [
                'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500&h=500&fit=crop'
            ],
            'KitchenAid Stand Mixer': [
                'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=500&h=500&fit=crop'
            ],
            
            # Beauty & Personal Care
            'SK-II Essence': [
                'https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=500&h=500&fit=crop'
            ],
            'Tom Ford Lipstick': [
                'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=500&h=500&fit=crop'
            ],
            'La Mer Cream': [
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop'
            ],
            'Clarisonic Face Brush': [
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop'
            ],
            'Dyson Hair Dryer': [
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop'
            ],
            'Chanel Perfume': [
                'https://images.unsplash.com/photo-1541643600914-78b084683601?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1541643600914-78b084683601?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1541643600914-78b084683601?w=500&h=500&fit=crop'
            ],
            'MAC Lipstick': [
                'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=500&h=500&fit=crop'
            ],
            'NARS Foundation': [
                'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=500&h=500&fit=crop'
            ],
            'Maybelline Mascara': [
                'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=500&h=500&fit=crop'
            ],
            'L\'Oreal Revitalift Serum': [
                'https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=500&h=500&fit=crop'
            ],
            
            # Sports & Outdoors
            'Resistance Bands': [
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop'
            ],
            'Yoga Mat': [
                'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=500&h=500&fit=crop'
            ],
            'REI Backpack': [
                'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&h=500&fit=crop'
            ],
            'Hydro Flask Bottle': [
                'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&h=500&fit=crop'
            ],
            'Garmin GPS Watch': [
                'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=500&h=500&fit=crop'
            ],
            'Coleman Tent': [
                'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&h=500&fit=crop'
            ],
            'Nike Training Shoes': [
                'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=500&h=500&fit=crop'
            ],
            'Patagonia Jacket': [
                'https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=500&h=500&fit=crop'
            ],
            'Yeti Cooler': [
                'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&h=500&fit=crop'
            ],
            'Peloton Bike': [
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop'
            ],
            
            # Books
            'The Alchemist': [
                'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=500&h=500&fit=crop'
            ],
            'Atomic Habits': [
                'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=500&h=500&fit=crop'
            ],
            
            # Groceries & Gourmet
            'Gourmet Coffee': [
                'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=500&h=500&fit=crop'
            ],
            
            # Health & Wellness
            'Meditation App Subscription': [
                'https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=500&h=500&fit=crop'
            ],
            'CBD Oil': [
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop'
            ],
            'Probiotics': [
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop'
            ],
            'Sleep Aid Supplements': [
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop'
            ],
            'Massage Gun': [
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop'
            ],
            'Yoga Block Set': [
                'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=500&h=500&fit=crop'
            ],
            'Essential Oils Set': [
                'https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=500&h=500&fit=crop'
            ],
            'Blood Pressure Monitor': [
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop'
            ],
            'Protein Powder': [
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop'
            ],
            'Multivitamin Supplement': [
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop'
            ]
        }
        
        # Fallback category images for products not specifically mapped
        fallback_images = {
            'Electronics': [
                'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1518717758536-85ae29035b6d?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=500&h=500&fit=crop'
            ],
            'Fashion': [
                'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1445205170230-053b83016050?w=500&h=500&fit=crop'
            ],
            'Home & Kitchen': [
                'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=500&h=500&fit=crop'
            ],
            'Beauty & Personal Care': [
                'https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=500&h=500&fit=crop'
            ],
            'Sports & Outdoors': [
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop'
            ],
            'Books': [
                'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=500&h=500&fit=crop'
            ],
            'Groceries & Gourmet': [
                'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=500&h=500&fit=crop'
            ],
            'Health & Wellness': [
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=500&h=500&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop'
            ]
        }

        products = Product.objects.filter(is_active=True)
        for product in products:
            if not product.images.exists():
                # Try to find specific product mapping first
                image_urls = None
                mapping_used = "fallback"
                
                for product_key, urls in product_specific_images.items():
                    if product_key.lower() in product.name.lower():
                        image_urls = urls
                        mapping_used = f"specific ({product_key})"
                        break
                
                # If no specific mapping found, use category fallback
                if image_urls is None:
                    category_name = product.category.name
                    if category_name in fallback_images:
                        image_urls = fallback_images[category_name]
                        mapping_used = f"category ({category_name})"
                    else:
                        self.stdout.write(f'  - No image mapping for {product.name} (category: {category_name})')
                        continue
                
                # Add primary image
                image_url = random.choice(image_urls)
                image_data = self.download_image(image_url)
                if image_data:
                    ProductImage.objects.create(
                        product=product,
                        image=ContentFile(image_data, name=f'{product.sku}_primary.jpg'),
                        alt_text=f'{product.name} - Primary Image',
                        is_primary=True,
                        sort_order=0
                    )
                    
                    # Add 1-3 additional images
                    additional_images = random.randint(1, 3)
                    for i in range(additional_images):
                        additional_url = random.choice(image_urls)
                        additional_data = self.download_image(additional_url)
                        if additional_data:
                            ProductImage.objects.create(
                                product=product,
                                image=ContentFile(additional_data, name=f'{product.sku}_additional_{i+1}.jpg'),
                                alt_text=f'{product.name} - Additional Image {i+1}',
                                is_primary=False,
                                sort_order=i+1
                            )
                    
                    self.stdout.write(f'  ✓ Added images for {product.name} (using {mapping_used})')
                else:
                    self.stdout.write(f'  ✗ Failed to download images for {product.name}')

    def add_profile_images(self):
        """Add profile photos for users"""
        self.stdout.write('Adding profile photos...')
        
        profile_image_urls = [
            'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&h=200&fit=crop&crop=face',
            'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&h=200&fit=crop&crop=face',
            'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=200&h=200&fit=crop&crop=face',
            'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=200&h=200&fit=crop&crop=face',
            'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&h=200&fit=crop&crop=face',
            'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=200&h=200&fit=crop&crop=face',
            'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=200&h=200&fit=crop&crop=face',
            'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=200&h=200&fit=crop&crop=face',
            'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=200&h=200&fit=crop&crop=face',
            'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&h=200&fit=crop&crop=face'
        ]

        profiles = Profile.objects.all()
        for profile in profiles:
            if profile.profile_picture.name == 'profile_pics/placeholder.jpg':
                image_url = random.choice(profile_image_urls)
                image_data = self.download_image(image_url)
                if image_data:
                    profile.profile_picture.save(
                        f'profile_{profile.user.username}.jpg',
                        ContentFile(image_data),
                        save=True
                    )
                    self.stdout.write(f'  ✓ Added profile photo for {profile.user.username}')
                else:
                    self.stdout.write(f'  ✗ Failed to download profile photo for {profile.user.username}')
            else:
                self.stdout.write(f'  - {profile.user.username} already has a profile photo')

    def download_image(self, url):
        """Download image from URL and return as bytes"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Process image with PIL to ensure proper format
            image = Image.open(io.BytesIO(response.content))
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Resize if too large
            if image.width > 800 or image.height > 800:
                image.thumbnail((800, 800), Image.Resampling.LANCZOS)
            
            # Save to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG', quality=85)
            img_byte_arr = img_byte_arr.getvalue()
            
            return img_byte_arr
            
        except Exception as e:
            self.stdout.write(f'    Error downloading image from {url}: {str(e)}')
            return None
