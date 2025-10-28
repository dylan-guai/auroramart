from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from online_store.item.models import Product, Category, Subcategory, Brand
from online_store.checkout.models import Order, OrderItem, Cart, CartItem
from online_store.profiles.models import Profile, Wishlist
from decimal import Decimal
from django.utils import timezone
import re
import random

def create_slug(text):
    """Create a valid slug from text"""
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

class Command(BaseCommand):
    help = 'Create comprehensive AuroraMart product catalog'

    def handle(self, *args, **options):
        # Create categories for AuroraMart
        categories_data = [
            {
                'name': 'Electronics',
                'description': 'Cutting-edge electronics and gadgets for modern living',
                'subcategories': [
                    'Smartphones', 'Laptops', 'Tablets', 'Audio & Headphones',
                    'Cameras', 'Gaming', 'Smart Home', 'Accessories'
                ]
            },
            {
                'name': 'Fashion',
                'description': 'Trendy fashion for men and women',
                'subcategories': [
                    'Men\'s Clothing', 'Women\'s Clothing', 'Shoes', 'Bags & Accessories',
                    'Jewelry', 'Watches', 'Activewear', 'Formal Wear'
                ]
            },
            {
                'name': 'Home & Kitchen',
                'description': 'Everything for your home and kitchen',
                'subcategories': [
                    'Furniture', 'Kitchen Appliances', 'Cookware', 'Home Decor',
                    'Bedding', 'Bath', 'Storage', 'Lighting'
                ]
            },
            {
                'name': 'Beauty & Personal Care',
                'description': 'Premium beauty and personal care products',
                'subcategories': [
                    'Skincare', 'Makeup', 'Hair Care', 'Fragrances',
                    'Men\'s Grooming', 'Bath & Body', 'Tools & Accessories', 'Health'
                ]
            },
            {
                'name': 'Sports & Outdoors',
                'description': 'Gear for active lifestyle and outdoor adventures',
                'subcategories': [
                    'Fitness Equipment', 'Outdoor Gear', 'Sports Apparel', 'Footwear',
                    'Water Sports', 'Winter Sports', 'Team Sports', 'Accessories'
                ]
            },
            {
                'name': 'Books',
                'description': 'Books for every reader and interest',
                'subcategories': [
                    'Fiction', 'Non-Fiction', 'Children\'s Books', 'Educational',
                    'Cookbooks', 'Art & Design', 'Business', 'Health & Wellness'
                ]
            },
            {
                'name': 'Groceries & Gourmet',
                'description': 'Fresh groceries and gourmet food items',
                'subcategories': [
                    'Fresh Produce', 'Meat & Seafood', 'Dairy & Eggs', 'Pantry Staples',
                    'Beverages', 'Snacks', 'International Foods', 'Organic & Health'
                ]
            },
            {
                'name': 'Health & Wellness',
                'description': 'Products for health and wellness',
                'subcategories': [
                    'Supplements', 'Medical Devices', 'Personal Care', 'Fitness',
                    'Mental Health', 'Senior Care', 'Baby Care', 'Pet Care'
                ]
            }
        ]

        # Create brands
        brands_data = [
            'Apple', 'Samsung', 'Sony', 'LG', 'Nike', 'Adidas', 'Uniqlo', 'Zara',
            'IKEA', 'KitchenAid', 'Dyson', 'Philips', 'L\'Oreal', 'Maybelline',
            'NARS', 'MAC', 'Under Armour', 'Puma', 'Canon', 'Nikon', 'Microsoft',
            'Google', 'Amazon', 'Tesla', 'BMW', 'Mercedes', 'Rolex', 'Omega',
            'Chanel', 'Gucci', 'Louis Vuitton', 'Hermes', 'Prada', 'Versace'
        ]

        # Create categories and subcategories
        created_categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'slug': create_slug(cat_data['name']),
                    'description': cat_data['description'],
                    'is_active': True,
                    'sort_order': len(created_categories)
                }
            )
            created_categories[cat_data['name']] = category
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))
            
            # Create subcategories
            for subcat_name in cat_data['subcategories']:
                subcategory, created = Subcategory.objects.get_or_create(
                    name=subcat_name,
                    category=category,
                    defaults={
                        'slug': create_slug(subcat_name),
                        'description': f'{subcat_name} products',
                        'is_active': True
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created subcategory: {subcategory.name}'))

        # Create brands
        created_brands = {}
        for brand_name in brands_data:
            brand, created = Brand.objects.get_or_create(
                name=brand_name,
                defaults={
                    'slug': create_slug(brand_name),
                    'description': f'{brand_name} products',
                    'is_active': True
                }
            )
            created_brands[brand_name] = brand
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created brand: {brand.name}'))

        # Create products for each category
        product_templates = {
            'Electronics': [
                ('iPhone 15 Pro', 'Latest iPhone with advanced camera system', 999.99),
                ('Samsung Galaxy S24', 'Premium Android smartphone', 899.99),
                ('MacBook Air M3', 'Lightweight laptop for professionals', 1299.99),
                ('Sony WH-1000XM5', 'Noise-cancelling headphones', 399.99),
                ('Canon EOS R6', 'Professional mirrorless camera', 2499.99),
                ('PlayStation 5', 'Next-gen gaming console', 499.99),
                ('Apple Watch Series 9', 'Advanced smartwatch', 399.99),
                ('iPad Pro 12.9"', 'Professional tablet', 1099.99),
                ('AirPods Pro 2', 'Wireless earbuds with ANC', 249.99),
                ('Dell XPS 13', 'Ultrabook for productivity', 1199.99),
            ],
            'Fashion': [
                ('Nike Air Max 270', 'Comfortable running shoes', 150.99),
                ('Adidas Ultraboost 22', 'Performance running shoes', 180.99),
                ('Uniqlo Heattech T-Shirt', 'Thermal base layer', 19.99),
                ('Zara Blazer', 'Professional blazer', 89.99),
                ('Levi\'s 501 Jeans', 'Classic denim jeans', 79.99),
                ('Rolex Submariner', 'Luxury diving watch', 8999.99),
                ('Chanel No. 5', 'Iconic fragrance', 129.99),
                ('Gucci Handbag', 'Designer leather handbag', 2899.99),
                ('Ray-Ban Aviator', 'Classic sunglasses', 154.99),
                ('North Face Jacket', 'Outdoor winter jacket', 199.99),
            ],
            'Home & Kitchen': [
                ('KitchenAid Stand Mixer', 'Professional kitchen mixer', 299.99),
                ('Dyson V15 Vacuum', 'Cordless vacuum cleaner', 649.99),
                ('IKEA Dining Table', 'Modern dining table', 199.99),
                ('Instant Pot Duo', 'Multi-cooker appliance', 99.99),
                ('Le Creuset Dutch Oven', 'Enameled cast iron pot', 249.99),
                ('Philips Hue Bulbs', 'Smart LED light bulbs', 49.99),
                ('Nespresso Machine', 'Coffee maker', 199.99),
                ('Vitamix Blender', 'High-performance blender', 399.99),
                ('Tempur-Pedic Pillow', 'Memory foam pillow', 89.99),
                ('Roomba i7+', 'Robot vacuum cleaner', 599.99),
            ],
            'Beauty & Personal Care': [
                ('L\'Oreal Revitalift Serum', 'Anti-aging serum', 29.99),
                ('Maybelline Mascara', 'Volumizing mascara', 9.99),
                ('NARS Foundation', 'Full coverage foundation', 49.99),
                ('MAC Lipstick', 'Matte lipstick', 19.99),
                ('Chanel Perfume', 'Luxury fragrance', 129.99),
                ('Dyson Hair Dryer', 'Professional hair dryer', 399.99),
                ('Clarisonic Face Brush', 'Sonic cleansing brush', 199.99),
                ('La Mer Cream', 'Luxury moisturizer', 299.99),
                ('Tom Ford Lipstick', 'High-end lipstick', 54.99),
                ('SK-II Essence', 'Premium skincare essence', 199.99),
            ],
            'Sports & Outdoors': [
                ('Peloton Bike', 'Interactive exercise bike', 1495.99),
                ('Yeti Cooler', 'Premium cooler', 299.99),
                ('Patagonia Jacket', 'Sustainable outdoor jacket', 199.99),
                ('Nike Training Shoes', 'Versatile athletic shoes', 120.99),
                ('Coleman Tent', 'Family camping tent', 149.99),
                ('Garmin GPS Watch', 'Sports tracking watch', 299.99),
                ('Hydro Flask Bottle', 'Insulated water bottle', 34.99),
                ('REI Backpack', 'Hiking backpack', 129.99),
                ('Yoga Mat', 'Premium yoga mat', 49.99),
                ('Resistance Bands', 'Workout resistance bands', 19.99),
            ],
            'Books': [
                ('Atomic Habits', 'Self-improvement book', 16.99),
                ('The Seven Husbands of Evelyn Hugo', 'Fiction novel', 14.99),
                ('Cookbook: Salt Fat Acid Heat', 'Culinary guide', 24.99),
                ('Educated', 'Memoir', 16.99),
                ('The Psychology of Money', 'Finance book', 18.99),
                ('Where the Crawdads Sing', 'Mystery novel', 15.99),
                ('Becoming', 'Michelle Obama memoir', 19.99),
                ('The Subtle Art of Not Giving a F*ck', 'Self-help book', 17.99),
                ('Sapiens', 'History book', 20.99),
                ('The Alchemist', 'Philosophical novel', 13.99),
            ],
            'Groceries & Gourmet': [
                ('Organic Avocados', 'Fresh organic avocados', 4.99),
                ('Wild Salmon Fillet', 'Fresh wild salmon', 24.99),
                ('Artisanal Cheese', 'Premium cheese selection', 18.99),
                ('Extra Virgin Olive Oil', 'Cold-pressed olive oil', 12.99),
                ('Organic Quinoa', 'Superfood grain', 8.99),
                ('Dark Chocolate', 'Premium dark chocolate', 9.99),
                ('Fresh Berries', 'Mixed berry selection', 6.99),
                ('Craft Beer', 'Local craft beer', 12.99),
                ('Organic Honey', 'Raw organic honey', 14.99),
                ('Gourmet Coffee', 'Single-origin coffee', 16.99),
            ],
            'Health & Wellness': [
                ('Multivitamin Supplement', 'Daily multivitamin', 19.99),
                ('Protein Powder', 'Whey protein powder', 29.99),
                ('Blood Pressure Monitor', 'Digital BP monitor', 49.99),
                ('Essential Oils Set', 'Aromatherapy oils', 39.99),
                ('Yoga Block Set', 'Yoga practice blocks', 24.99),
                ('Massage Gun', 'Muscle recovery tool', 99.99),
                ('Sleep Aid Supplements', 'Natural sleep support', 16.99),
                ('Probiotics', 'Digestive health support', 22.99),
                ('CBD Oil', 'Cannabidiol tincture', 49.99),
                ('Meditation App Subscription', 'Mindfulness app', 9.99),
            ]
        }

        # Create products
        product_count = 0
        for category_name, products in product_templates.items():
            category = created_categories[category_name]
            subcategories = category.subcategories.all()
            
            for product_name, description, price in products:
                # Create multiple variations of each product
                for i in range(5):  # 5 variations per product
                    variation_name = f"{product_name}"
                    if i > 0:
                        variation_name += f" - Variation {i+1}"
                    
                    # Random brand selection
                    brand = random.choice(list(created_brands.values()))
                    
                    # Random subcategory
                    subcategory = random.choice(subcategories) if subcategories else None
                    
                    # Random pricing variation
                    price_variation = price * random.uniform(0.8, 1.2)
                    
                    product, created = Product.objects.get_or_create(
                        sku=f"{category_name[:3].upper()}{product_count:04d}",
                        defaults={
                            'name': variation_name,
                            'slug': create_slug(variation_name),
                            'description': f"{description} - Premium quality product for discerning customers.",
                            'short_description': description,
                            'price': Decimal(str(round(price_variation, 2))),
                            'category': category,
                            'subcategory': subcategory,
                            'brand': brand,
                            'stock_quantity': random.randint(10, 100),
                            'is_active': True,
                            'average_rating': round(random.uniform(3.5, 5.0), 1),
                            'review_count': random.randint(5, 150)
                        }
                    )
                    
                    if created:
                        product_count += 1
                        if product_count % 50 == 0:
                            self.stdout.write(self.style.SUCCESS(f'Created {product_count} products...'))

        self.stdout.write(self.style.SUCCESS(f'Created {product_count} products total!'))
        self.stdout.write(self.style.SUCCESS('AuroraMart product catalog created successfully!'))
