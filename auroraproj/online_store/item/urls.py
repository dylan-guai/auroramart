from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'item'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('<int:product_id>/', views.product_detail, name='product_detail'),
    path('<int:product_id>/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('<int:product_id>/add-review/', views.add_review, name='add_review'),
    # Category and subcategory URLs
    path('category/<slug:category_slug>/', views.category_detail, name='category_detail'),
    path('category/<slug:category_slug>/<slug:subcategory_slug>/', views.subcategory_detail, name='subcategory_detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 