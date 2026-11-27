import uuid

import requests
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe


class TurnstileWidget(forms.Widget):
    template_name = None  # manually rendered

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        return mark_safe(
            f"""
            <div
                class="cf-turnstile"
                data-sitekey="{settings.TURNSTILE_SITE_KEY}"
                data-size="compact"
                data-callback="onSuccess"
                data-error-callback="onError"
                data-expired-callback="onExpired"
                data-timeout-callback="onExpired"
                data-unsupported-callback="onUnsupported"
            ></div>
            """
        )

    def value_from_datadict(self, data, files, name):
        # Turnstile puts response in 'cf-turnstile-response' on HTML element
        return data.get("cf-turnstile-response")


class TurnstileField(forms.Field):
    def __init__(self, **kwargs):
        self._base_required = kwargs.get("required", True)
        super().__init__(**kwargs)
        self.request = None  # Will be set by the form
        self.set_enabled(settings.TURNSTILE_ENABLED)

    def set_enabled(self, enabled):
        self.required = self._base_required and enabled
        if enabled:
            self.widget = TurnstileWidget()
        else:
            # dummy, turnstile is disabled
            self.widget = forms.HiddenInput()

    def clean(self, value):
        value = super().clean(value)

        if self.required and value is None:
            raise ValidationError("This field is required")
        elif not settings.TURNSTILE_ENABLED:
            return value
        # no need to make an api call during testing (ci or local)
        elif settings.IN_CI or settings.TESTING:
            # check secret key and site key
            if not settings.TURNSTILE_SECRET_KEY.startswith("1x"):
                raise ValidationError("Invalid turnstile response")

            if not (settings.TURNSTILE_SITE_KEY.startswith("1x") or settings.TURNSTILE_SITE_KEY.startswith("2x")):
                raise ValidationError("Invalid turnstile response")

            return value

        # get the client IP
        remote_ip = self._get_client_ip()

        # https://developers.cloudflare.com/turnstile/get-started/server-side-validation/
        payload = {
            "secret": settings.TURNSTILE_SECRET_KEY,
            "response": value,
            "idempotency_key": str(uuid.uuid4()),
        }

        # optional, but important
        if remote_ip:
            payload["remoteip"] = remote_ip

        try:
            turnstile_resp = requests.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                json=payload,
                timeout=10,  # 10s otherwise it'll just hang forever (worst case)
            )
        except requests.exceptions.RequestException as e:
            raise ValidationError("Invalid turnstile response") from e

        if not turnstile_resp.ok:
            raise ValidationError("Invalid turnstile response")

        try:
            turnstile_data = turnstile_resp.json()
        except ValueError as e:
            raise ValidationError("Invalid turnstile response") from e

        if not turnstile_data.get("success", False):
            raise ValidationError("Invalid turnstile response")

        # validate hostname to prevent token substitution attacks
        hostname = turnstile_data.get("hostname", "")
        expected_hostname = getattr(settings, "TURNSTILE_EXPECTED_HOSTNAME", None)
        if expected_hostname and hostname != expected_hostname:
            raise ValidationError("Invalid turnstile response")

        # success!
        return value

    def _get_client_ip(self):
        """Get the client's IP address from the request."""
        if not self.request:
            return None

        # check x-real-ip header first (proxied requests)
        x_real_ip = self.request.headers.get("x-real-ip")
        if x_real_ip:
            return x_real_ip.split(",", 1)[0].strip()

        # fall back to REMOTE_ADDR
        return self.request.META.get("REMOTE_ADDR")
