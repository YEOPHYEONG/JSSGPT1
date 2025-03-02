# langchain_app/apps.py
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class LangchainAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'langchain_app'

    def ready(self):
        try:
            import langchain_app.signals
            logger.info("langchain_app.signals imported successfully.")
        except Exception as e:
            logger.error("Error importing langchain_app.signals: %s", e)
