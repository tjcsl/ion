SECRET_DATABASE_URL="postgres://ion:pwd@postgres:5432/ion"
SESSION_REDIS_HOST = "redis"
SESSION_REDIS_PORT = 6379
SESSION_REDIS_DB = 0
SESSION_REDIS_PREFIX = "ion:session"
SESSION_REDIS = {"host": SESSION_REDIS_HOST, "port": SESSION_REDIS_PORT, "db": SESSION_REDIS_DB, "prefix": SESSION_REDIS_PREFIX}
CACHEOPS_REDIS = {"host": "redis", "port": 6379, "db": 1, "socket_timeout": 1}
CACHES = {
    "default": {
        "BACKEND": "redis_cache.RedisCache",
        "LOCATION": "redis:6379",
        "OPTIONS": {"PARSER_CLASS": "redis.connection.HiredisParser", "PICKLE_VERSION": 4},
        "KEY_PREFIX": "ion",
    }
}
CHANNEL_LAYERS = {"default": {"BACKEND": "channels_redis.core.RedisChannelLayer", "CONFIG": {"hosts": [("redis", 6379)]}}}
#notfish
MASTER_PASSWORD='argon2$argon2id$v=19$m=512,t=2,p=2$1JlK3UX2Ho1we5W8MPo2hA$cCXDGVyPD6olv/PbxdDTlA'
CELERY_BROKER_URL="redis://redis:6379/0"