from django.core.cache.backends.dummy import DummyCache as DjangoDummyCache


class DummyCache(DjangoDummyCache):
    def delete_pattern(self, key, version=None):
        pass
