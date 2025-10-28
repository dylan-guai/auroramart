from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from loyalty.models import LoyaltyTier, LoyaltyReward


class Command(BaseCommand):
    help = 'Set up loyalty program tiers and sample rewards'

    def handle(self, *args, **options):
        self.stdout.write('Setting up loyalty program...')
        
        # Create loyalty tiers
        tiers_data = [
            {
                'name': 'bronze',
                'display_name': 'Bronze',
                'min_points': 0,
                'max_points': 499,
                'point_multiplier': 1.00,
                'discount_percentage': 0.00,
                'free_shipping': False,
                'priority_support': False,
                'exclusive_access': False,
                'color': '#CD7F32',
                'icon': 'medal',
                'description': 'Welcome to AuroraMart! Start earning points with every purchase.',
            },
            {
                'name': 'silver',
                'display_name': 'Silver',
                'min_points': 500,
                'max_points': 1499,
                'point_multiplier': 1.25,
                'discount_percentage': 5.00,
                'free_shipping': False,
                'priority_support': False,
                'exclusive_access': False,
                'color': '#C0C0C0',
                'icon': 'medal',
                'description': 'Silver tier members enjoy 25% bonus points and 5% discount on all purchases.',
            },
            {
                'name': 'gold',
                'display_name': 'Gold',
                'min_points': 1500,
                'max_points': 4999,
                'point_multiplier': 1.50,
                'discount_percentage': 10.00,
                'free_shipping': True,
                'priority_support': False,
                'exclusive_access': False,
                'color': '#FFD700',
                'icon': 'medal',
                'description': 'Gold tier members get 50% bonus points, 10% discount, and free shipping on all orders.',
            },
            {
                'name': 'platinum',
                'display_name': 'Platinum',
                'min_points': 5000,
                'max_points': 9999,
                'point_multiplier': 2.00,
                'discount_percentage': 15.00,
                'free_shipping': True,
                'priority_support': True,
                'exclusive_access': False,
                'color': '#E5E4E2',
                'icon': 'medal',
                'description': 'Platinum members enjoy double points, 15% discount, free shipping, and priority support.',
            },
            {
                'name': 'diamond',
                'display_name': 'Diamond',
                'min_points': 10000,
                'max_points': None,
                'point_multiplier': 2.50,
                'discount_percentage': 20.00,
                'free_shipping': True,
                'priority_support': True,
                'exclusive_access': True,
                'color': '#B9F2FF',
                'icon': 'medal',
                'description': 'Diamond tier members get 2.5x points, 20% discount, free shipping, priority support, and exclusive access to new products.',
            },
        ]
        
        for tier_data in tiers_data:
            tier, created = LoyaltyTier.objects.get_or_create(
                name=tier_data['name'],
                defaults=tier_data
            )
            if created:
                self.stdout.write(f'Created {tier.display_name} tier')
            else:
                self.stdout.write(f'{tier.display_name} tier already exists')
        
        # Create sample rewards
        rewards_data = [
            {
                'name': '$5 Off Next Purchase',
                'description': 'Get $5 off your next order',
                'reward_type': 'discount',
                'points_cost': 500,
                'discount_amount': 5.00,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=365),
                'max_redemptions': 1000,
            },
            {
                'name': '$10 Off Next Purchase',
                'description': 'Get $10 off your next order',
                'reward_type': 'discount',
                'points_cost': 1000,
                'discount_amount': 10.00,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=365),
                'max_redemptions': 500,
            },
            {
                'name': 'Free Shipping',
                'description': 'Free shipping on your next order',
                'reward_type': 'free_shipping',
                'points_cost': 300,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=365),
                'max_redemptions': 2000,
            },
            {
                'name': '20% Off Next Purchase',
                'description': 'Get 20% off your next order',
                'reward_type': 'discount',
                'points_cost': 2000,
                'discount_percentage': 20.00,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=365),
                'max_redemptions': 100,
            },
            {
                'name': 'Birthday Bonus',
                'description': 'Special birthday bonus points',
                'reward_type': 'points_bonus',
                'points_cost': 100,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=365),
                'max_redemptions': 5000,
            },
        ]
        
        for reward_data in rewards_data:
            reward, created = LoyaltyReward.objects.get_or_create(
                name=reward_data['name'],
                defaults=reward_data
            )
            if created:
                self.stdout.write(f'Created reward: {reward.name}')
            else:
                self.stdout.write(f'Reward already exists: {reward.name}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up loyalty program!')
        )
