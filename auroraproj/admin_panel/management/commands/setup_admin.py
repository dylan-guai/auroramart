from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from admin_panel.models import AdminRole, AdminUser

class Command(BaseCommand):
    help = 'Set up initial admin roles and create super admin user'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin', help='Super admin username')
        parser.add_argument('--email', type=str, default='admin@auroramart.com', help='Super admin email')
        parser.add_argument('--password', type=str, default='admin123!', help='Super admin password')

    def handle(self, *args, **options):
        self.stdout.write('Setting up AuroraMart admin system...')
        
        # Create admin roles
        self.create_admin_roles()
        
        # Create super admin user
        self.create_super_admin(
            username=options['username'],
            email=options['email'],
            password=options['password']
        )
        
        self.stdout.write(
            self.style.SUCCESS('Admin system setup complete!')
        )

    def create_admin_roles(self):
        """Create predefined admin roles with permissions"""
        
        # Super Admin role
        superadmin_role, created = AdminRole.objects.get_or_create(
            name='superadmin',
            defaults={
                'description': 'Full access to all admin functions',
                'is_active': True
            }
        )
        
        # Admin role
        admin_role, created = AdminRole.objects.get_or_create(
            name='admin',
            defaults={
                'description': 'General admin access with most permissions',
                'is_active': True
            }
        )
        
        # Merchandiser role
        merchandiser_role, created = AdminRole.objects.get_or_create(
            name='merchandiser',
            defaults={
                'description': 'Product catalog and pricing management',
                'is_active': True
            }
        )
        
        # Inventory Manager role
        inventory_role, created = AdminRole.objects.get_or_create(
            name='inventory',
            defaults={
                'description': 'Inventory and stock management',
                'is_active': True
            }
        )
        
        # CRM Manager role
        crm_role, created = AdminRole.objects.get_or_create(
            name='crm',
            defaults={
                'description': 'Customer relationship management',
                'is_active': True
            }
        )
        
        # Data Analyst role
        analyst_role, created = AdminRole.objects.get_or_create(
            name='analyst',
            defaults={
                'description': 'Analytics and reporting access',
                'is_active': True
            }
        )
        
        # Assign permissions to roles
        self.assign_permissions_to_roles()
        
        self.stdout.write('✓ Admin roles created')

    def assign_permissions_to_roles(self):
        """Assign appropriate permissions to each role"""
        
        # Get content types for our models
        try:
            from online_store.item.models import Product, Category, Subcategory, Brand
            from online_store.profiles.models import Profile
            from online_store.checkout.models import Order, Cart, CartItem
            
            # Product permissions
            product_permissions = Permission.objects.filter(
                content_type__model__in=['product', 'category', 'subcategory', 'brand']
            )
            
            # User permissions
            user_permissions = Permission.objects.filter(
                content_type__model__in=['user', 'group']
            )
            
            # Order permissions
            order_permissions = Permission.objects.filter(
                content_type__model__in=['order', 'cart', 'cartitem']
            )
            
            # Profile permissions
            profile_permissions = Permission.objects.filter(
                content_type__model='profile'
            )
            
            # Super Admin gets all permissions
            superadmin_role = AdminRole.objects.get(name='superadmin')
            superadmin_role.permissions.set(Permission.objects.all())
            
            # Admin gets most permissions
            admin_role = AdminRole.objects.get(name='admin')
            admin_role.permissions.set(
                product_permissions | order_permissions | profile_permissions
            )
            
            # Merchandiser gets product permissions
            merchandiser_role = AdminRole.objects.get(name='merchandiser')
            merchandiser_role.permissions.set(product_permissions)
            
            # Inventory Manager gets product permissions (for stock management)
            inventory_role = AdminRole.objects.get(name='inventory')
            inventory_role.permissions.set(product_permissions)
            
            # CRM Manager gets order and profile permissions
            crm_role = AdminRole.objects.get(name='crm')
            crm_role.permissions.set(order_permissions | profile_permissions)
            
            # Data Analyst gets read permissions
            analyst_role = AdminRole.objects.get(name='analyst')
            read_permissions = Permission.objects.filter(codename__startswith='view_')
            analyst_role.permissions.set(read_permissions)
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Could not assign permissions: {e}')
            )

    def create_super_admin(self, username, email, password):
        """Create super admin user"""
        
        # Create or get user
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': 'Super',
                'last_name': 'Admin',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True
            }
        )
        
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(f'✓ Created super admin user: {username}')
        else:
            self.stdout.write(f'✓ Super admin user already exists: {username}')
        
        # Create AdminUser profile
        admin_user, created = AdminUser.objects.get_or_create(
            user=user,
            defaults={
                'role': AdminRole.objects.get(name='superadmin'),
                'employee_id': 'ADMIN001',
                'department': 'IT',
                'is_active_admin': True
            }
        )
        
        if created:
            self.stdout.write(f'✓ Created admin profile for: {username}')
        else:
            self.stdout.write(f'✓ Admin profile already exists for: {username}')
        
        # Display login information
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('ADMIN LOGIN CREDENTIALS'))
        self.stdout.write('='*50)
        self.stdout.write(f'Username: {username}')
        self.stdout.write(f'Password: {password}')
        self.stdout.write(f'Email: {email}')
        self.stdout.write('='*50)
        self.stdout.write('Access the admin panel at: /admin-panel/')
        self.stdout.write('='*50)
