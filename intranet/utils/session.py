from redis_sessions.session import SessionStore as BaseSessionStore


class SessionStore(BaseSessionStore):  # pylint: disable=abstract-method
    def load(self):
        orig_session_key = self._session_key
        data = super().load()

        if self._session_key is None and orig_session_key is not None:
            # If django-redis-sessions encounters ANY errors while loading
            # the session, it ignores them and sets self._session_key to
            # None. This makes Django's session middleware delete the
            # "sessionid" cookie in the user's browser.
            # The effect here is to clear the session of any user who visits
            # while Redis is down, logging them out.
            # So if django-redis-sessions set self._session_key to None, we
            # take special action.

            # First, we temporarily reset self._session_key.
            self._session_key = orig_session_key
            # Then we ping the server. If we encounter an error here, the
            # the session ID won't get cleared in the user's browser during the
            # response (because we just reset it above).
            self.server.ping()
            # If we got here, the server is reachable and it was probably some
            # other error.
            self._session_key = None

        return data
