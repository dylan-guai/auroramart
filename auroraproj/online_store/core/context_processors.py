from online_store.item.models import Category
from online_store.checkout.models import Cart

def categories_context(request):
    """Make categories and cart info available globally in templates"""
    context = {
        'categories': Category.objects.filter(is_active=True)
    }
    
    # Add cart total quantity for authenticated users
    if request.user.is_authenticated:
        try:
            # Check if user has a profile (customer users)
            profile = request.user.profile
            cart = Cart.objects.get(buyer=profile)
            context['total_quantity'] = cart.total_items
        except (Cart.DoesNotExist, AttributeError):
            # Cart doesn't exist or user doesn't have profile (admin users)
            context['total_quantity'] = 0
    else:
        context['total_quantity'] = 0
    
    return context