import os

if os.getenv("PRODUCTION", "FALSE") == "TRUE":
    from .production import *
else:
    from .local import *
