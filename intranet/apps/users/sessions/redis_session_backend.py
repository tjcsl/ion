# By Instagram
from django.contrib.sessions.backends.base import SessionBase, CreateError
from django.conf import settings
from django.utils.encoding import force_unicode
import redis

class SessionStore(SessionBase):
    """ Redis store for sessions"""

    def __init__(self, session_key=None):
        self.redis = redis.Redis(
            host = settings.SESSION_REDIS_HOST,
            port = settings.SESSION_REDIS_PORT,
            socket_timeout = settings.REDIS_SOCKET_TIMEOUT,
        )
        super(SessionStore, self).__init__(session_key)

    @classmethod
    def _get_key_for_redis(self, session_key):
        return 'sessionstore:%s' % session_key

    def _redis_key(self):
        return self.__class__._get_key_for_redis(self.session_key)

    def load(self):
        session_data = self.redis.get(self._redis_key())
        if session_data is not None:
            return self.decode(force_unicode(session_data))
        else:
            self.create()
            return {}

    def create(self):
        max_attempts = 10
        attempt = 0
        while True:
            self.session_key = self._get_new_session_key()
            session_dict = self._get_session(no_load=True)
            session_data = self.encode(session_dict)

            was_created = self.redis.setnx(self._redis_key(),
                                           session_data)
            if was_created:
                self.redis.expire(self._redis_key(),
                                  settings.SESSION_COOKIE_AGE)
                self.modified = True
                self._session_cache = session_dict
                return
            else:
                # extremely unlikely
                if attempt == max_attempts:
                    raise CreateError
                else:
                    attempt += 1
                    continue

    def save(self, must_create=False):
        if must_create:
            self.create()
        else:
            encoded_data = self.encode(self._session)
            self.redis.setex(self._redis_key(), encoded_data, settings.SESSION_COOKIE_AGE)

    def exists(self, session_key):
        return self.redis.exists(self.__class__._get_key_for_redis(session_key))

    def delete(self, session_key=None):
        to_delete = (session_key or self.session_key)
        redis_key = self.__class__._get_key_for_redis(to_delete)
        self.redis.delete(redis_key)
