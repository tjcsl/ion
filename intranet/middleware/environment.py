# -*- coding: utf-8 -*-

import logging
import os

logger = logging.getLogger(__name__)


class KerberosCacheMiddleware(object):
    """Reloads the KRB5CCNAME environmental variable from the session for potential use in future
    LDAP requests.

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
        """Propogate KRB5CCNAME session variable to the environmental variable."""
        if "KRB5CCNAME" in request.session:
            # It is important to check that the environmental variable
            # matches the session variable because environmentals stay
            # on the worker after requests.
            if "KRB5CCNAME" in os.environ:
                if os.environ["KRB5CCNAME"] != request.session["KRB5CCNAME"]:
                    logger.debug("Reloading KRB5CCNAME environmental variable from session.")
                    os.environ["KRB5CCNAME"] = request.session["KRB5CCNAME"]
            else:
                logger.debug("KRB5CCNAME environmental variable not set - setting it to KRB5CCNAME from session vars.")
                os.environ["KRB5CCNAME"] = request.session["KRB5CCNAME"]
        return None
