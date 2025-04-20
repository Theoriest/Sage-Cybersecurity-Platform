from django.apps import AppConfig

class AwarenessConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Awareness'
    verbose_name = 'Security Awareness'
    
    def ready(self):
        """Import signals when app is ready"""
        import Awareness.signals
