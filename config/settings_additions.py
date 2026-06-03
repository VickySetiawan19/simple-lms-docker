"""
Tambahkan konfigurasi ini ke config/settings.py yang sudah ada.
Letakkan di bagian bawah file settings.py.
"""

import os

# =============================================
# INSTALLED APPS TAMBAHAN
# =============================================
# Tambahkan ke INSTALLED_APPS yang sudah ada:
# 'django_celery_beat',   # Celery Beat scheduler
# 'analytics',            # MongoDB analytics app

# =============================================
# REDIS CACHE CONFIGURATION
# =============================================
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://redis:6379/0"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "RETRY_ON_TIMEOUT": True,
            "MAX_CONNECTIONS": 50,
        },
        "KEY_PREFIX": "lms",
        "TIMEOUT": int(os.environ.get("CACHE_TTL", 300)),  # 5 menit default
    }
}

# Gunakan Redis juga untuk session
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# =============================================
# MONGODB CONFIGURATION
# =============================================
MONGODB_SETTINGS = {
    "db": os.environ.get("MONGO_DB_NAME", "lms_analytics"),
    "host": os.environ.get("MONGO_HOST", "mongodb"),
    "port": int(os.environ.get("MONGO_PORT", 27017)),
}

# =============================================
# CELERY CONFIGURATION
# =============================================
CELERY_BROKER_URL = os.environ.get(
    "CELERY_BROKER_URL",
    "amqp://guest:guest@rabbitmq:5672//"
)
CELERY_RESULT_BACKEND = os.environ.get(
    "CELERY_RESULT_BACKEND",
    "redis://redis:6379/1"
)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Jakarta"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 menit max per task

# =============================================
# EMAIL CONFIGURATION (untuk Celery email task)
# =============================================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# =============================================
# RATE LIMITING
# =============================================
RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", 60))

# Ratelimit cache backend
RATELIMIT_USE_CACHE = "default"  # gunakan Redis cache