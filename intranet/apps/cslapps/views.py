from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from ..auth.decorators import deny_restricted
from .models import App


@login_required
@deny_restricted
def redirect_to_app(request):
    """Redirect the user to the specified app's authorization or main page, based on latest access time."""

    app_id = request.GET.get("id")
    try:
        app = App.objects.get(id=app_id)
        if app.visible_to(request.user):
            if not app.auth_url == "" and request.COOKIES.get("accessed_csl-app_" + app_id, "") != "1":
                response = redirect(app.auth_url)
                response.set_cookie("accessed_csl-app_" + app_id, "1", max_age=60 * 60 * 24)
                return response
            else:
                return redirect(app.url)
        messages.error(request, "You are not authorized to access the requested app.")
        return redirect("/")

    except App.DoesNotExist:
        messages.error(request, "The requested app does not exist.")
        return redirect("/")
