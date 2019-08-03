from django.conf import settings

from .utils import get_start_date


def start_date(request):
    """ Add the start date to the context for eighth admins.

        Args:
            request: The request object

        Returns:
            The start date if an eighth_admin, an empty dictionary
            otherwise.

    """

    if request.user and request.user.is_authenticated and request.user.is_eighth_admin:
        return {"admin_start_date": get_start_date(request)}

    return {}


def enable_waitlist(request):
    """ Add whether the waitlist is enabled to the context.

        Args:
            request: The request object

        Returns:
            bool: Whether the waitlist is enabled.

    """

    return {"waitlist_enabled": settings.ENABLE_WAITLIST}


def absence_count(request):
    """ Add the absence count to the context for students.

        Args:
            request: The request object

        Returns:
            Number of absences that a student has if
            a student, an empty dictionary otherwise.

    """

    if request.user and request.user.is_authenticated and request.user.is_student:
        absence_info = request.user.absence_info()
        num_absences = absence_info.count()
        show_notif = False
        if num_absences and not request.session.get("eighth_absence_notif_seen", False):
            show_notif = any(signup.in_clear_absence_period() for signup in absence_info)

            if show_notif:
                request.session["eighth_absence_notif_seen"] = True

        return {"eighth_absence_count": num_absences, "eighth_absence_notif": show_notif}

    return {}
