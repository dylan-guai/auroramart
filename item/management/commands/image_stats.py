from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from item.models import Product, Category, ProductImage
from profiles.models import Profile
import os

class Command(BaseCommand):
    help = 'Display image statistics and manage images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show image statistics',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Remove unused images',
        )

    def handle(self, *args, **options):
        if options['stats']:
            self.show_stats()
        if options['cleanup']:
            self.cleanup_images()

    def show_stats(self):
        """Display image statistics"""
        self.stdout.write('📊 IMAGE STATISTICS')
        self.stdout.write('=' * 50)
        
        # Category images
        categories_with_images = Category.objects.filter(image__isnull=False).count()
        total_categories = Category.objects.count()
        self.stdout.write(f'Categories with images: {categories_with_images}/{total_categories}')
        
        # Product images
        products_with_images = Product.objects.filter(images__isnull=False).distinct().count()
        total_products = Product.objects.count()
        total_product_images = ProductImage.objects.count()
        self.stdout.write(f'Products with images: {products_with_images}/{total_products}')
        self.stdout.write(f'Total product images: {total_product_images}')
        
        # Profile photos
        profiles_with_photos = Profile.objects.exclude(profile_picture='profile_pics/placeholder.jpg').count()
        total_profiles = Profile.objects.count()
        self.stdout.write(f'Profiles with photos: {profiles_with_photos}/{total_profiles}')
        
        # Media directory size
        try:
            media_path = default_storage.path('')
            if os.path.exists(media_path):
                total_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                               for dirpath, dirnames, filenames in os.walk(media_path)
                               for filename in filenames)
                size_mb = total_size / (1024 * 1024)
                self.stdout.write(f'Total media size: {size_mb:.2f} MB')
        except Exception as e:
            self.stdout.write(f'Could not calculate media size: {e}')

    def cleanup_images(self):
        """Remove unused images (placeholder implementation)"""
        self.stdout.write('🧹 IMAGE CLEANUP')
        self.stdout.write('=' * 50)
        self.stdout.write('This feature would remove unused images.')
        self.stdout.write('Implementation pending - use with caution!')
