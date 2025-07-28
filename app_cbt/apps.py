from django.apps import AppConfig


class AppCbtConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_cbt'


class app_cbt_AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_cbt'

    def ready(self):
        import app_cbt.signals  # Pastikan path-nya benar