from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid


class LoyaltyTier(models.Model):
    """Loyalty program tiers with different benefits"""
    TIER_CHOICES = [
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
        ('diamond', 'Diamond'),
    ]
    
    name = models.CharField(max_length=20, choices=TIER_CHOICES, unique=True)
    display_name = models.CharField(max_length=50)
    min_points = models.PositiveIntegerField()
    max_points = models.PositiveIntegerField(null=True, blank=True)
    point_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=1.00)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    free_shipping = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    exclusive_access = models.BooleanField(default=False)
    color = models.CharField(max_length=7, default='#CD7F32')  # Bronze color
    icon = models.CharField(max_length=50, default='medal')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['min_points']
        verbose_name = 'Loyalty Tier'
        verbose_name_plural = 'Loyalty Tiers'
    
    def __str__(self):
        return f"{self.display_name} ({self.min_points}+ points)"
    
    @property
    def next_tier(self):
        """Get the next tier in the hierarchy"""
        return LoyaltyTier.objects.filter(
            min_points__gt=self.min_points,
            is_active=True
        ).order_by('min_points').first()


class LoyaltyAccount(models.Model):
    """Customer loyalty account with points and tier information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loyalty_account')
    points_balance = models.PositiveIntegerField(default=0)
    lifetime_points = models.PositiveIntegerField(default=0)
    current_tier = models.ForeignKey(LoyaltyTier, on_delete=models.SET_NULL, null=True, blank=True)
    join_date = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Loyalty Account'
        verbose_name_plural = 'Loyalty Accounts'
    
    def __str__(self):
        return f"{self.user.username} - {self.current_tier.display_name if self.current_tier else 'No Tier'}"
    
    def add_points(self, points, source='purchase', description=''):
        """Add points to the account"""
        if points <= 0:
            return False
        
        # Apply tier multiplier
        multiplier = self.current_tier.point_multiplier if self.current_tier else 1.00
        adjusted_points = int(points * multiplier)
        
        self.points_balance += adjusted_points
        self.lifetime_points += adjusted_points
        self.save()
        
        # Create transaction record
        LoyaltyTransaction.objects.create(
            account=self,
            points=adjusted_points,
            transaction_type='earned',
            source=source,
            description=description
        )
        
        # Check for tier upgrade
        self.check_tier_upgrade()
        
        return True
    
    def redeem_points(self, points, description=''):
        """Redeem points from the account"""
        if points <= 0 or points > self.points_balance:
            return False
        
        self.points_balance -= points
        self.save()
        
        # Create transaction record
        LoyaltyTransaction.objects.create(
            account=self,
            points=-points,
            transaction_type='redeemed',
            source='redemption',
            description=description
        )
        
        return True
    
    def check_tier_upgrade(self):
        """Check and upgrade tier if eligible"""
        if not self.current_tier:
            # Assign first tier
            first_tier = LoyaltyTier.objects.filter(is_active=True).order_by('min_points').first()
            if first_tier and self.lifetime_points >= first_tier.min_points:
                self.current_tier = first_tier
                self.save()
                return True
        
        # Check for tier upgrade
        next_tier = self.current_tier.next_tier if self.current_tier else None
        if next_tier and self.lifetime_points >= next_tier.min_points:
            self.current_tier = next_tier
            self.save()
            
            # Create tier upgrade notification
            LoyaltyNotification.objects.create(
                account=self,
                notification_type='tier_upgrade',
                title=f'Congratulations! You\'ve reached {next_tier.display_name} tier!',
                message=f'You\'ve been upgraded to {next_tier.display_name} tier with {next_tier.discount_percentage}% discount and exclusive benefits!',
                is_read=False
            )
            
            return True
        
        return False
    
    @property
    def points_to_next_tier(self):
        """Calculate points needed to reach next tier"""
        if not self.current_tier:
            first_tier = LoyaltyTier.objects.filter(is_active=True).order_by('min_points').first()
            if first_tier:
                return max(0, first_tier.min_points - self.lifetime_points)
            return 0
        
        next_tier = self.current_tier.next_tier
        if next_tier:
            return max(0, next_tier.min_points - self.lifetime_points)
        
        return 0
    
    @property
    def tier_progress_percentage(self):
        """Calculate tier progress percentage"""
        if not self.current_tier:
            return 0
        
        next_tier = self.current_tier.next_tier
        if not next_tier:
            return 100
        
        current_points = self.lifetime_points
        tier_range = next_tier.min_points - self.current_tier.min_points
        progress = current_points - self.current_tier.min_points
        
        return min(100, max(0, (progress / tier_range) * 100))


class LoyaltyTransaction(models.Model):
    """Record of all loyalty point transactions"""
    TRANSACTION_TYPES = [
        ('earned', 'Earned'),
        ('redeemed', 'Redeemed'),
        ('expired', 'Expired'),
        ('adjusted', 'Adjusted'),
    ]
    
    SOURCE_CHOICES = [
        ('purchase', 'Purchase'),
        ('review', 'Product Review'),
        ('referral', 'Referral'),
        ('birthday', 'Birthday Bonus'),
        ('promotion', 'Promotion'),
        ('redemption', 'Redemption'),
        ('admin', 'Admin Adjustment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(LoyaltyAccount, on_delete=models.CASCADE, related_name='transactions')
    points = models.IntegerField()  # Positive for earned, negative for redeemed
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    description = models.TextField(blank=True)
    order = models.ForeignKey('checkout.Order', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Loyalty Transaction'
        verbose_name_plural = 'Loyalty Transactions'
    
    def __str__(self):
        return f"{self.account.user.username} - {self.points} points ({self.transaction_type})"


class LoyaltyReward(models.Model):
    """Rewards available for redemption"""
    REWARD_TYPES = [
        ('discount', 'Discount'),
        ('free_shipping', 'Free Shipping'),
        ('free_product', 'Free Product'),
        ('points_bonus', 'Points Bonus'),
        ('exclusive_access', 'Exclusive Access'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    reward_type = models.CharField(max_length=20, choices=REWARD_TYPES)
    points_cost = models.PositiveIntegerField()
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    free_product = models.ForeignKey('item.Product', on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    max_redemptions = models.PositiveIntegerField(null=True, blank=True)
    current_redemptions = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['points_cost']
        verbose_name = 'Loyalty Reward'
        verbose_name_plural = 'Loyalty Rewards'
    
    def __str__(self):
        return f"{self.name} ({self.points_cost} points)"
    
    @property
    def is_available(self):
        """Check if reward is available for redemption"""
        if not self.is_active:
            return False
        
        if self.max_redemptions and self.current_redemptions >= self.max_redemptions:
            return False
        
        from django.utils import timezone
        now = timezone.now()
        return self.valid_from <= now <= self.valid_until


class LoyaltyRedemption(models.Model):
    """Record of reward redemptions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('used', 'Used'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(LoyaltyAccount, on_delete=models.CASCADE, related_name='redemptions')
    reward = models.ForeignKey(LoyaltyReward, on_delete=models.CASCADE)
    points_used = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    redeemed_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    order = models.ForeignKey('checkout.Order', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-redeemed_at']
        verbose_name = 'Loyalty Redemption'
        verbose_name_plural = 'Loyalty Redemptions'
    
    def __str__(self):
        return f"{self.account.user.username} - {self.reward.name}"
    
    @property
    def is_expired(self):
        """Check if redemption has expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at


class LoyaltyNotification(models.Model):
    """Notifications for loyalty program activities"""
    NOTIFICATION_TYPES = [
        ('tier_upgrade', 'Tier Upgrade'),
        ('points_earned', 'Points Earned'),
        ('points_expiring', 'Points Expiring'),
        ('reward_available', 'Reward Available'),
        ('reward_redeemed', 'Reward Redeemed'),
        ('promotion', 'Promotion'),
    ]
    
    account = models.ForeignKey(LoyaltyAccount, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Loyalty Notification'
        verbose_name_plural = 'Loyalty Notifications'
    
    def __str__(self):
        return f"{self.account.user.username} - {self.title}"


class LoyaltyAnalytics(models.Model):
    """Analytics data for loyalty program performance"""
    date = models.DateField()
    total_accounts = models.PositiveIntegerField(default=0)
    active_accounts = models.PositiveIntegerField(default=0)
    total_points_earned = models.PositiveIntegerField(default=0)
    total_points_redeemed = models.PositiveIntegerField(default=0)
    total_redemptions = models.PositiveIntegerField(default=0)
    tier_distribution = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['date']
        ordering = ['-date']
        verbose_name = 'Loyalty Analytics'
        verbose_name_plural = 'Loyalty Analytics'
    
    def __str__(self):
        return f"Loyalty Analytics - {self.date}"
