from django.apps import AppConfig


class LoyaltyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'loyalty'
    verbose_name = 'Loyalty Program'
    
    def ready(self):
        import loyalty.signals
