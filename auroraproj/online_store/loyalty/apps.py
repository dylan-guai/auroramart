from django.apps import AppConfig


class LoyaltyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'online_store.loyalty'
    verbose_name = 'Loyalty Program'
    
    def ready(self):
        import online_store.loyalty.signals
