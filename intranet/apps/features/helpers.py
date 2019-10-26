from typing import Optional


def get_feature_context(request) -> Optional[str]:
    """Given a Django request, returns the 'context' that should be used to select feature
    announcements to display (one of ``dashboard``, ``login``, ``eighth_signup``, or ``None``).

    Args:
        request: The current request object.

    Returns:
        The "context" that should be used to select feature announcements for the page requested
        by ``request``.

    """

    if request.resolver_match is not None:
        view_name = request.resolver_match.view_name

        if view_name == "index":
            return "dashboard" if request.user.is_authenticated else "login"
        elif view_name == "login":
            return "login"
        elif view_name == "eighth_signup":
            return "eighth_signup"

    return None
