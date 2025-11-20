import logging

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .views import get_emerg

logger = logging.getLogger(__name__)


@api_view(("GET",))
# @renderer_classes((JSONRenderer,))
@permission_classes((AllowAny,))
def emerg_status(request):
    return Response(get_emerg())
