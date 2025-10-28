from django.contrib import admin
from .models import Profile, CustomerPreference, CustomerSegment, Wishlist

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'age', 'gender', 'occupation', 'demographics_complete', 'is_onboarding_complete']
    list_filter = ['gender', 'occupation', 'education', 'income_range', 'is_onboarding_complete']
    search_fields = ['user__username', 'user__email', 'first_name', 'last_name']
    readonly_fields = ['profile_id', 'created_at', 'updated_at', 'prediction_updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'first_name', 'last_name', 'profile_id', 'biography', 'profile_picture')
        }),
        ('Demographics (AI Prediction)', {
            'fields': ('age', 'gender', 'occupation', 'education', 'income_range')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'address', 'city', 'state', 'zip_code', 'country')
        }),
        ('AI Prediction Results', {
            'fields': ('predicted_category_id', 'prediction_confidence', 'prediction_updated_at'),
            'classes': ('collapse',)
        }),
        ('Onboarding Status', {
            'fields': ('is_onboarding_complete', 'onboarding_completed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(CustomerPreference)
class CustomerPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'category_id', 'preference_score', 'interaction_count', 'last_interaction']
    list_filter = ['last_interaction']
    search_fields = ['user__username', 'category_id']
    ordering = ['-preference_score']

@admin.register(CustomerSegment)
class CustomerSegmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'predicted_category_id', 'description']
    search_fields = ['name', 'description']

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'added_at']
    list_filter = ['added_at']
    search_fields = ['user__username', 'product__name']
    ordering = ['-added_at']
