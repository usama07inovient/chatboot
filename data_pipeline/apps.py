from django.apps import AppConfig


class DataPipelineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'data_pipeline'
    def ready(self):
        import data_pipeline.signals  # Import signals when the app is ready