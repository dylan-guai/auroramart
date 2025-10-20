from django.urls import path
from . import views

app_name = 'loyalty'

urlpatterns = [
    # Customer-facing loyalty pages
    path('', views.loyalty_dashboard, name='dashboard'),
    path('rewards/', views.loyalty_rewards, name='rewards'),
    path('rewards/<int:reward_id>/redeem/', views.redeem_reward, name='redeem_reward'),
    path('transactions/', views.loyalty_transactions, name='transactions'),
    path('notifications/', views.loyalty_notifications, name='notifications'),
    path('tiers/', views.loyalty_tiers, name='tiers'),
    
    # API endpoints
    path('api/points/', views.loyalty_api_points, name='api_points'),
    path('api/tiers/', views.loyalty_api_tier_info, name='api_tiers'),
]
