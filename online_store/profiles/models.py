from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import uuid

class Profile(models.Model):
    """Extended user profile with demographics for AI prediction"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Basic Profile Information (keeping your existing structure)
    first_name = models.CharField(max_length=100, default="NA")
    last_name = models.CharField(max_length=100, default="NA")
    profile_id = models.UUIDField(default=uuid.uuid4, editable=False)
    biography = models.CharField(blank=True, max_length=255)
    profile_picture = models.ImageField(upload_to='profile_pics', default='profile_pics/placeholder.jpg')
    address = models.CharField(blank=True, max_length=255)
    
    # Demographics for Decision Tree Model (AuroraMart AI Requirements)
    age = models.PositiveIntegerField(blank=True, null=True, help_text="Age for AI prediction")
    household_size = models.PositiveIntegerField(blank=True, null=True, default=1, help_text="Number of people in household")
    has_children = models.BooleanField(default=False, help_text="Whether user has children")
    monthly_income_sgd = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Monthly income in SGD")
    
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    
    EMPLOYMENT_STATUS_CHOICES = [
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
        ('Self-employed', 'Self-employed'),
        ('Student', 'Student'),
        ('Retired', 'Retired'),
        ('Unemployed', 'Unemployed'),
    ]
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS_CHOICES, blank=True)
    
    OCCUPATION_CHOICES = [
        ('Tech', 'Tech'),
        ('Sales', 'Sales'),
        ('Service', 'Service'),
        ('Admin', 'Admin'),
        ('Education', 'Education'),
        ('Skilled Trades', 'Skilled Trades'),
        ('Other', 'Other'),
    ]
    occupation = models.CharField(max_length=20, choices=OCCUPATION_CHOICES, blank=True)
    
    EDUCATION_CHOICES = [
        ('Secondary', 'Secondary'),
        ('Diploma', 'Diploma'),
        ('Bachelor', 'Bachelor'),
        ('Master', 'Master'),
        ('Doctorate', 'Doctorate'),
    ]
    education = models.CharField(max_length=20, choices=EDUCATION_CHOICES, blank=True)
    
    INCOME_CHOICES = [
        ('low', 'Below $2,000'),
        ('medium', '$2,000 - $5,000'),
        ('high', '$5,000 - $10,000'),
        ('very_high', 'Above $10,000'),
    ]
    income_range = models.CharField(max_length=20, choices=INCOME_CHOICES, blank=True)
    
    # Contact Information (enhanced from your original)
    phone_number = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=100, default='Singapore')
    
    # AI Prediction Results (new for AuroraMart)
    predicted_category_id = models.PositiveIntegerField(null=True, blank=True, help_text="AI predicted preferred category ID")
    prediction_confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    prediction_updated_at = models.DateTimeField(null=True, blank=True)
    
    # Profile Completion Tracking
    is_onboarding_complete = models.BooleanField(default=False)
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}"
    
    @property
    def demographics_complete(self):
        """Check if all required demographics are filled for AI prediction"""
        required_fields = ['age', 'gender', 'occupation', 'education', 'income_range']
        return all(getattr(self, field) for field in required_fields)
    
    @property
    def full_name(self):
        """Return user's full name"""
        if self.first_name != "NA" and self.last_name != "NA":
            return f"{self.first_name} {self.last_name}"
        return self.user.username
    
    def complete_onboarding(self):
        """Mark onboarding as complete"""
        self.is_onboarding_complete = True
        self.onboarding_completed_at = timezone.now()
        self.save()

class CustomerPreference(models.Model):
    """Track customer preferences and behavior for AI recommendations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='preferences')
    category_id = models.PositiveIntegerField(help_text="Category ID for preference tracking")
    preference_score = models.DecimalField(max_digits=5, decimal_places=4, default=0.0000)
    interaction_count = models.PositiveIntegerField(default=0)
    last_interaction = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'category_id']
    
    def __str__(self):
        return f"{self.user.username} - Category {self.category_id}: {self.preference_score}"

class CustomerSegment(models.Model):
    """AI-predicted customer segments"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    predicted_category_id = models.PositiveIntegerField(help_text="Primary category for this segment")
    characteristics = models.JSONField(default=dict, help_text="Store segment characteristics")
    
    def __str__(self):
        return self.name

class Wishlist(models.Model):
    """User's saved/wishlist items"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey('item.Product', on_delete=models.CASCADE, related_name='wishlist_items')
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'product']
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

# Signal to create profile when user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create profile automatically when user is created"""
    if created:
        Profile.objects.create(user=instance)

# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     """Save profile when user is saved - but don't override existing data"""
#     if hasattr(instance, 'profile'):
#         # Only save if the profile has no demographic data to avoid overriding
#         profile = instance.profile
#         if not profile.age and not profile.gender and not profile.occupation:
#             profile.save()