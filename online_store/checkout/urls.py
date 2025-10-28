from django.urls import path
from . import views

app_name = 'checkout'

urlpatterns = [
    path('', views.checkout, name='checkout'),
    path('success/<int:order_id>/', views.checkout_success, name='checkout_success'),
    path('cart/', views.cart_view, name='cart_view'),
    # AJAX endpoints for cart management
    path('cart/item/<int:item_id>/update/', views.update_cart_item, name='update_cart_item'),
    path('cart/item/<int:item_id>/remove/', views.remove_cart_item, name='remove_cart_item'),
    # Loyalty rewards endpoints
    path('cart/loyalty/points/', views.apply_loyalty_points, name='apply_loyalty_points'),
    path('cart/loyalty/reward/<int:reward_id>/', views.apply_loyalty_reward, name='apply_loyalty_reward'),
    path('cart/loyalty/remove/', views.remove_loyalty_discount, name='remove_loyalty_discount'),
]