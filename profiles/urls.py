from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path('', views.profile, name='profile'),
    path('edit/', views.edit_profile, name='edit_profile'),
    path('demographics/', views.demographics_form, name='demographics_form'),
    path('orders/', views.order_history, name='order_history'),
    path('orders/track/<int:order_id>/', views.order_tracking, name='order_tracking'),
    path('orders/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('orders/return/<int:order_id>/', views.return_order, name='return_order'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('reorder/<int:order_id>/', views.reorder, name='reorder'),
]
