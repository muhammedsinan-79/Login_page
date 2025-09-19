from django.apps import AppConfig
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)


class LoginAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'loginapp'


    def ready(self):
        keys = cache.keys("throttle_email_*")
        if keys:
            cache.delete_many(keys)
            logger.info(f"Cleared {len(keys)} throttle keys on startup")
        else:
            logger.info("No throttle keys to clear on startup")
