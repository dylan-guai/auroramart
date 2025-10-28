from django.contrib import admin
from .models import SearchFilter, SearchHistory, ProductView, SearchSuggestion

@admin.register(SearchFilter)
class SearchFilterAdmin(admin.ModelAdmin):
    list_display = ['user', 'filter_type', 'filter_value', 'is_active', 'created_at']
    list_filter = ['filter_type', 'is_active', 'created_at']
    search_fields = ['user__username', 'filter_value']
    readonly_fields = ['created_at']

@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'query', 'results_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['query', 'user__username', 'session_id']
    readonly_fields = ['created_at']

@admin.register(ProductView)
class ProductViewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'time_spent', 'created_at']
    list_filter = ['created_at']
    search_fields = ['product__name', 'user__username', 'session_id']
    readonly_fields = ['created_at']

@admin.register(SearchSuggestion)
class SearchSuggestionAdmin(admin.ModelAdmin):
    list_display = ['query', 'popularity_score', 'category_id', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['query']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-popularity_score']