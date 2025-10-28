from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('about/', views.about_us, name='about_us'),
    path('careers/', views.careers, name='careers'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_of_service, name='terms_of_service'),
    path('help/', views.help_center, name='help_center'),
    path('shipping/', views.shipping_info, name='shipping_info'),
    path('returns/', views.returns, name='returns'),
    path('contact/', views.contact_us, name='contact_us'),
]
