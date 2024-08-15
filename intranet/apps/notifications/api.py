import os

from push_notifications.models import WebPushDevice
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from intranet.apps.notifications.serializers import WebPushDeviceSerializer

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class GetApplicationServerKey(APIView):
    def get(self, request):
        # Load the VAPID application server key from a file
        file_path = os.path.join(PROJECT_ROOT, "keys", "webpush", "ApplicationServerKey.key")
        with open(file_path, encoding="utf-8") as file:
            server_key = file.read().strip()
        return Response({"applicationServerKey": server_key}, status=status.HTTP_200_OK)


class GetWebpushSubscriptionStatus(APIView):
    def post(self, request):
        endpoint = request.data.get("endpoint")
        try:
            subscription = WebPushDevice.objects.filter(registration_id=endpoint).first()
        except WebPushDevice.DoesNotExist:
            return Response({"status": False}, status=status.HTTP_200_OK)
        if subscription is not None and subscription.active:
            return Response({"status": True}, status=status.HTTP_200_OK)
        else:
            return Response({"status": False}, status=status.HTTP_200_OK)


class WebpushSubscribeDevice(generics.CreateAPIView):
    queryset = WebPushDevice.objects.all()
    serializer_class = WebPushDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WebpushUpdateDevice(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        old_registration_id = request.data.get("old_registration_id")

        try:
            subscription = WebPushDevice.objects.filter(registration_id=old_registration_id).first()
            subscription.registration_id = request.data.get("registration_id")
            subscription.p256dh = request.data.get("p256dh")
            subscription.auth = request.data.get("auth")
            subscription.save()

            return Response({"message": "Subscription updated"}, status=status.HTTP_200_OK)
        except WebPushDevice.DoesNotExist:
            return Response({"error": "Subscription not found"}, status=status.HTTP_404_NOT_FOUND)


class WebpushUnsubscribeDevice(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        endpoint = request.data.get("endpoint")

        try:
            subscription = WebPushDevice.objects.filter(registration_id=endpoint).first()
            subscription.delete()
            # Check if the user no longer has any (0) subscribed devices left
            if WebPushDevice.objects.filter(user=request.user).count() == 0:
                request.user.push_notification_preferences.is_subscribed = False
            else:
                request.user.push_notification_preferences.is_subscribed = True
            return Response({"message": "Subscription deleted"}, status=status.HTTP_200_OK)
        except WebPushDevice.DoesNotExist:
            return Response({"error": "Subscription not found"}, status=status.HTTP_404_NOT_FOUND)
