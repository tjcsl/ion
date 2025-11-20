from typing import Any, Optional

USER_SETTINGS = ...  # type: Any
DEFAULTS = ...  # type: Any
MANDATORY = ...  # type: Any
IMPORT_STRINGS = ...  # type: Any

def perform_import(val, setting_name): ...
def import_from_string(val, setting_name): ...

class OAuth2ProviderSettings:
    user_settings = ...  # type: Any
    defaults = ...  # type: Any
    import_strings = ...  # type: Any
    mandatory = ...  # type: Any
    def __init__(self, user_settings: Optional[Any] = ..., defaults: Optional[Any] = ..., import_strings: Optional[Any] = ..., mandatory: Optional[Any] = ...) -> None: ...
    def __getattr__(self, attr): ...
    def validate_setting(self, attr, val): ...

oauth2_settings = ...  # type: Any
