from oauth2_provider.models import AccessToken

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from ..auth.decorators import deny_restricted
from .models import App


@login_required
@deny_restricted
def redirect_to_app(request):
    """Redirect the user to the specified app's authorization or main page, based on OAuth token validity,
    if available, or latest access time."""

    app_id = request.GET.get("id")
    try:
        app = App.objects.get(id=app_id)
        if app.visible_to(request.user):
            if app.auth_url:
                if not app.oauth_application:
                    if request.COOKIES.get("accessed_csl-app_" + app_id, "") != "1":
                        response = redirect(app.auth_url)
                        response.set_cookie("accessed_csl-app_" + app_id, "1", max_age=60 * 60 * 24)
                        return response
                    return redirect(app.url)
                else:
                    last_token = (
                        AccessToken.objects.filter(user=request.user, application=app.oauth_application)
                        .order_by("-expires")
                        .values_list("token", "expires")
                        .first()
                    )
                    if last_token and last_token.is_valid():
                        return redirect(app.url)
                    return redirect(app.auth_url)
            return redirect(app.url)
        messages.error(request, "You are not authorized to access the requested app.")
        return redirect("/")

    except App.DoesNotExist:
        messages.error(request, "The requested app does not exist.")
        return redirect("/")
