from oauth2_provider.models import AbstractApplication

from django.db import models


class CSLApplication(AbstractApplication):
    """Extends the default OAuth Application model to add CSL-specific information about an OAuth application.

    Attributes:
        sanctioned (bool): Whether the application is sanctioned by the tjCSL.

    """

    sanctioned = models.BooleanField(default=False)
