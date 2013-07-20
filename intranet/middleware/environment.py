import os
import logging
# from django.shortcuts import render, redirect

logger = logging.getLogger(__name__)


class SetKerberosCache(object):
    """Reloads the KRB5CCNAME environmental variable from the session
    for potential use in future LDAP requests.

    For a login request, the KRB5CCNAME environmental variable has
    already been set in the authentication backend, but for all other
    requests, it must be reset from the Kerberos cache stored in a
    user's session. Otherwise all requests to a a particular Gunicorn
    worker would use the Kerberos cache of the user who most recently
    logged in through that worker.

    The environmental variable must be set by middleware so it is
    available for requests to any view and so each view does not have
    to load the environmental variable. The LDAP wrapper
    (intranet.db.ldap_db) cannot set the environmental variable because
    it does not have access to the current session (request.session).

    """
    def process_request(self, request):
        if "KRB5CCNAME" in request.session and "KRB5CCNAME" not in os.environ:
            logger.debug("Reloading KRB5CCNAME environmental \
                          variable from session")
            os.environ["KRB5CCNAME"] = request.session["KRB5CCNAME"]
        return None
