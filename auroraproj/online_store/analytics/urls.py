from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Analytics dashboard and pages
    path('', views.analytics_dashboard, name='dashboard'),
    path('revenue/', views.analytics_revenue, name='revenue'),
    path('customers/', views.analytics_customers, name='customers'),
    path('products/', views.analytics_products, name='products'),
    path('marketing/', views.analytics_marketing, name='marketing'),
    path('ai-performance/', views.analytics_ai_performance, name='ai_performance'),
    
    # API endpoints
    path('api/data/', views.analytics_api_data, name='api_data'),
]
