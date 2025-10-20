from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.search, name='search'),
    path('autocomplete/', views.search_autocomplete, name='search_autocomplete'),
    path('suggestions/', views.search_suggestions, name='search_suggestions'),
]
