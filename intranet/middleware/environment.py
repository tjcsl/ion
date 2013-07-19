import os
import logging
# from django.shortcuts import render, redirect

logger = logging.getLogger(__name__)


class SetKerberosCache(object):
    def process_request(self, request):
        if "KRB5CCNAME" in request.session and "KRB5CCNAME" not in os.environ:
            logger.debug("Reloading KRB5CCNAME environmental \
                          variable from session")
            os.environ["KRB5CCNAME"] = request.session["KRB5CCNAME"]
        return None
