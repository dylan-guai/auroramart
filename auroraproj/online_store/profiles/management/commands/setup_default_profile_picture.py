import os
import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.conf import settings

class Command(BaseCommand):
    help = 'Set up a default profile picture for new users'

    def handle(self, *args, **kwargs):
        self.stdout.write('Setting up default profile picture...')
        
        # Create profile_pics directory if it doesn't exist
        profile_pics_dir = os.path.join(settings.MEDIA_ROOT, 'profile_pics')
        os.makedirs(profile_pics_dir, exist_ok=True)
        
        # Default profile picture URL (a generic user avatar)
        default_picture_url = 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&h=200&fit=crop&crop=face'
        
        # Download the default profile picture
        try:
            response = requests.get(default_picture_url)
            response.raise_for_status()
            
            # Save as placeholder.jpg
            placeholder_path = os.path.join(profile_pics_dir, 'placeholder.jpg')
            with open(placeholder_path, 'wb') as f:
                f.write(response.content)
            
            self.stdout.write(
                self.style.SUCCESS('✅ Default profile picture set up successfully!')
            )
            self.stdout.write(f'   Saved to: {placeholder_path}')
            
        except requests.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to download default profile picture: {e}')
            )
            # Create a simple placeholder if download fails
            self.create_simple_placeholder(profile_pics_dir)
    
    def create_simple_placeholder(self, profile_pics_dir):
        """Create a simple placeholder if download fails"""
        try:
            # Create a simple colored square as placeholder
            from PIL import Image, ImageDraw
            
            # Create a 200x200 image with a light gray background
            img = Image.new('RGB', (200, 200), color='#f0f0f0')
            draw = ImageDraw.Draw(img)
            
            # Draw a simple user icon
            # Head (circle)
            draw.ellipse([60, 40, 140, 120], fill='#d0d0d0', outline='#a0a0a0', width=2)
            
            # Body (rectangle)
            draw.rectangle([80, 120, 120, 180], fill='#d0d0d0', outline='#a0a0a0', width=2)
            
            # Save the image
            placeholder_path = os.path.join(profile_pics_dir, 'placeholder.jpg')
            img.save(placeholder_path, 'JPEG', quality=85)
            
            self.stdout.write(
                self.style.SUCCESS('✅ Simple placeholder profile picture created!')
            )
            self.stdout.write(f'   Saved to: {placeholder_path}')
            
        except ImportError:
            self.stdout.write(
                self.style.WARNING('⚠️ PIL not available, skipping placeholder creation')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to create placeholder: {e}')
            )
