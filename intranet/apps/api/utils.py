from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response
from ..eighth import exceptions as eighth_exceptions 

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, eighth_exceptions.SignupException):
        response = Response({'details': exc.messages()}, status=status.HTTP_400_BAD_REQUEST)

    return response


