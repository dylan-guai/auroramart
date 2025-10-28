from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'online_store.analytics'
    verbose_name = 'Analytics Dashboard'
    
    def ready(self):
        import online_store.analytics.signals
