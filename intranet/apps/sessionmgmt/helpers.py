from .models import TrustedSession


def trust_session(request) -> None:
    """Creates a TrustedSession object for a given request's session, populating all the fields
    properly.

    Args:
        request: A request from the device/session that should be trusted.

    """
    device_type = "unknown"
    if request.user_agent.is_mobile:
        device_type = "mobile"
    if request.user_agent.is_tablet:
        device_type = "tablet"
    if request.user_agent.is_pc:
        device_type = "computer"

    description = ""
    if request.user_agent.browser.family != "Other":
        description += request.user_agent.browser.family

    showed_device = False
    if request.user_agent.device.family != "Other":
        if description:
            description += " on "
        showed_device = True

        description += request.user_agent.device.family

    if request.user_agent.os.family != "Other":
        if description:
            if showed_device:
                description += " running "
            else:
                description += " on "

        description += request.user_agent.os.family

    if not TrustedSession.objects.filter(user=request.user, session_key=request.session.session_key).exists():
        TrustedSession.objects.create(user=request.user, session_key=request.session.session_key, description=description, device_type=device_type)

    request.session.set_expiry(7 * 24 * 60 * 60)  # Trusted sessions expire after a week
