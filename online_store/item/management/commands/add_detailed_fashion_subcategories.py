from django.core.management.base import BaseCommand
from item.models import Category, Subcategory

class Command(BaseCommand):
    help = 'Add detailed subcategories for Fashion category'

    def handle(self, *args, **options):
        # Get the Fashion category
        try:
            fashion_category = Category.objects.get(name='Fashion')
        except Category.DoesNotExist:
            self.stdout.write(self.style.ERROR('Fashion category not found'))
            return

        # Define detailed subcategories for Fashion
        detailed_subcategories = [
            # Men's Clothing
            {
                'name': "Men's T-Shirts",
                'slug': 'mens-t-shirts',
                'description': 'Comfortable and stylish t-shirts for men'
            },
            {
                'name': "Men's Shirts",
                'slug': 'mens-shirts',
                'description': 'Dress shirts, casual shirts, and button-ups'
            },
            {
                'name': "Men's Pants",
                'slug': 'mens-pants',
                'description': 'Jeans, dress pants, and casual trousers'
            },
            {
                'name': "Men's Shorts",
                'slug': 'mens-shorts',
                'description': 'Casual and athletic shorts for men'
            },
            {
                'name': "Men's Jackets",
                'slug': 'mens-jackets',
                'description': 'Blazers, casual jackets, and outerwear'
            },
            {
                'name': "Men's Suits",
                'slug': 'mens-suits',
                'description': 'Formal suits and business attire'
            },
            {
                'name': "Men's Underwear",
                'slug': 'mens-underwear',
                'description': 'Boxers, briefs, and undershirts'
            },
            {
                'name': "Men's Sleepwear",
                'slug': 'mens-sleepwear',
                'description': 'Pajamas and sleepwear for men'
            },
            
            # Women's Clothing
            {
                'name': "Women's Tops",
                'slug': 'womens-tops',
                'description': 'Blouses, t-shirts, and casual tops'
            },
            {
                'name': "Women's Dresses",
                'slug': 'womens-dresses',
                'description': 'Casual, formal, and party dresses'
            },
            {
                'name': "Women's Pants",
                'slug': 'womens-pants',
                'description': 'Jeans, dress pants, and leggings'
            },
            {
                'name': "Women's Skirts",
                'slug': 'womens-skirts',
                'description': 'Mini, midi, and maxi skirts'
            },
            {
                'name': "Women's Shorts",
                'slug': 'womens-shorts',
                'description': 'Casual and athletic shorts for women'
            },
            {
                'name': "Women's Jackets",
                'slug': 'womens-jackets',
                'description': 'Blazers, cardigans, and outerwear'
            },
            {
                'name': "Women's Intimates",
                'slug': 'womens-intimates',
                'description': 'Bras, panties, and lingerie'
            },
            {
                'name': "Women's Sleepwear",
                'slug': 'womens-sleepwear',
                'description': 'Pajamas, nightgowns, and robes'
            },
            
            # Shoes
            {
                'name': "Men's Sneakers",
                'slug': 'mens-sneakers',
                'description': 'Athletic and casual sneakers for men'
            },
            {
                'name': "Men's Dress Shoes",
                'slug': 'mens-dress-shoes',
                'description': 'Oxfords, loafers, and formal shoes'
            },
            {
                'name': "Men's Boots",
                'slug': 'mens-boots',
                'description': 'Work boots, casual boots, and hiking boots'
            },
            {
                'name': "Women's Sneakers",
                'slug': 'womens-sneakers',
                'description': 'Athletic and casual sneakers for women'
            },
            {
                'name': "Women's Heels",
                'slug': 'womens-heels',
                'description': 'Pumps, stilettos, and heeled shoes'
            },
            {
                'name': "Women's Flats",
                'slug': 'womens-flats',
                'description': 'Ballet flats, loafers, and casual flats'
            },
            {
                'name': "Women's Boots",
                'slug': 'womens-boots',
                'description': 'Ankle boots, knee-high boots, and winter boots'
            },
            {
                'name': "Women's Sandals",
                'slug': 'womens-sandals',
                'description': 'Summer sandals and flip-flops'
            },
            
            # Accessories
            {
                'name': "Handbags",
                'slug': 'handbags',
                'description': 'Totes, crossbody bags, and clutches'
            },
            {
                'name': "Backpacks",
                'slug': 'backpacks',
                'description': 'School bags, travel backpacks, and daypacks'
            },
            {
                'name': "Wallets",
                'slug': 'wallets',
                'description': 'Men\'s and women\'s wallets and card holders'
            },
            {
                'name': "Belts",
                'slug': 'belts',
                'description': 'Leather belts, casual belts, and dress belts'
            },
            {
                'name': "Scarves",
                'slug': 'scarves',
                'description': 'Silk scarves, winter scarves, and fashion scarves'
            },
            {
                'name': "Hats",
                'slug': 'hats',
                'description': 'Baseball caps, beanies, and fashion hats'
            },
            
            # Jewelry
            {
                'name': "Necklaces",
                'slug': 'necklaces',
                'description': 'Chains, pendants, and statement necklaces'
            },
            {
                'name': "Earrings",
                'slug': 'earrings',
                'description': 'Studs, hoops, and drop earrings'
            },
            {
                'name': "Rings",
                'slug': 'rings',
                'description': 'Wedding rings, fashion rings, and statement rings'
            },
            {
                'name': "Bracelets",
                'slug': 'bracelets',
                'description': 'Charm bracelets, bangles, and cuffs'
            },
            {
                'name': "Watches",
                'slug': 'watches',
                'description': 'Analog watches, digital watches, and smartwatches'
            },
            
            # Activewear
            {
                'name': "Men's Activewear",
                'slug': 'mens-activewear',
                'description': 'Gym clothes, running gear, and athletic wear'
            },
            {
                'name': "Women's Activewear",
                'slug': 'womens-activewear',
                'description': 'Yoga pants, sports bras, and workout tops'
            },
            {
                'name': "Swimwear",
                'slug': 'swimwear',
                'description': 'Swimsuits, bikinis, and swim trunks'
            },
            {
                'name': "Athletic Shoes",
                'slug': 'athletic-shoes',
                'description': 'Running shoes, training shoes, and sports footwear'
            }
        ]

        # Create or update subcategories
        created_count = 0
        updated_count = 0

        for subcat_data in detailed_subcategories:
            subcategory, created = Subcategory.objects.get_or_create(
                category=fashion_category,
                slug=subcat_data['slug'],
                defaults={
                    'name': subcat_data['name'],
                    'description': subcat_data['description'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f"Created subcategory: {subcategory.name}")
            else:
                # Update existing subcategory
                subcategory.name = subcat_data['name']
                subcategory.description = subcat_data['description']
                subcategory.is_active = True
                subcategory.save()
                updated_count += 1
                self.stdout.write(f"Updated subcategory: {subcategory.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {len(detailed_subcategories)} subcategories: '
                f'{created_count} created, {updated_count} updated'
            )
        )
