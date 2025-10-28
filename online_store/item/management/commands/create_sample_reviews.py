from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from item.models import Product, ProductReview
import random

class Command(BaseCommand):
    help = 'Create sample reviews for testing sorting functionality'

    def handle(self, *args, **options):
        # Get some products and users
        products = Product.objects.filter(is_active=True, stock_quantity__gt=0)[:50]  # First 50 products
        users = User.objects.all()
        
        if not users.exists():
            self.stdout.write(self.style.ERROR('No users found. Please create users first.'))
            return
        
        if not products.exists():
            self.stdout.write(self.style.ERROR('No products found.'))
            return
        
        # Create reviews for random products
        reviews_created = 0
        
        for product in products:
            # Create 1-5 reviews per product
            num_reviews = random.randint(1, 5)
            
            for i in range(num_reviews):
                user = random.choice(users)
                
                # Check if user already reviewed this product
                if ProductReview.objects.filter(product=product, user=user).exists():
                    continue
                
                rating = random.randint(1, 5)
                title = f"Review for {product.name}"
                comment = f"This is a sample review for {product.name}. Rating: {rating} stars."
                
                ProductReview.objects.create(
                    product=product,
                    user=user,
                    rating=rating,
                    title=title,
                    comment=comment,
                    is_verified_purchase=random.choice([True, False])
                )
                
                reviews_created += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {reviews_created} sample reviews')
        )
        
        # Show some statistics
        total_reviews = ProductReview.objects.count()
        products_with_reviews = Product.objects.filter(reviews__isnull=False).distinct().count()
        
        self.stdout.write(f'Total reviews in database: {total_reviews}')
        self.stdout.write(f'Products with reviews: {products_with_reviews}')
        
        # Show top rated products
        top_rated = Product.objects.filter(
            is_active=True, 
            stock_quantity__gt=0,
            average_rating__gt=0
        ).order_by('-average_rating', '-review_count')[:5]
        
        self.stdout.write('\nTop 5 rated products:')
        for product in top_rated:
            self.stdout.write(f'  {product.name}: {product.average_rating} stars ({product.review_count} reviews)')
