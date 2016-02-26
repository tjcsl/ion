# -*- coding: utf-8 -*-

import logging

from django.contrib import messages

from ..db.ldap_db import LDAPConnection

logger = logging.getLogger(__name__)


class CheckLDAPBindMiddleware:

    def process_response(self, request, response):
        if not request.user.is_authenticated():
            # Nothing to check if user isn't already logged in
            return response

        if "_auth_user_backend" not in request.session:
            # Can't check the backend
            logger.debug("Can't check the auth user backend for an LDAP bind")
            return response

        auth_backend = request.session["_auth_user_backend"]
        kerberos_backend = "KerberosAuthenticationBackend"
        if (LDAPConnection().did_use_simple_bind() and auth_backend.startswith(kerberos_backend)):
            # if request.user.is_eighth_admin:
            #    logger.info("Simple bind being used: staying logged in because eighth admin.")
            #    return response
            logger.info("LDAP simple bind being used for {}".format(request.user if request.user else None))
            messages.error(request, "Access to directory information may be limited: LDAP issue. Try logging out and back in.")
            """
            logger.info("Simple bind being used: Destroying kerberos cache and logging out")

            try:
                kerberos_cache = request.session["KRB5CCNAME"]
                os.system("/usr/bin/kdestroy -c " + kerberos_cache)
            except KeyError:
                pass
            logout(request)

            response = redirect("login")
            url = response["Location"]
            response["Location"] = urls.add_get_parameters(
                url, {"next": request.path}, percent_encode=False)
            return response
            """
        return response
