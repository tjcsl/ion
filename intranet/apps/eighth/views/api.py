import logging
from datetime import datetime

from rest_framework import generics, permissions, status, views
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import Http404

from ..models import EighthActivity, EighthBlock, EighthScheduledActivity, EighthSignup
from ..serializers import (EighthActivityDetailSerializer, EighthActivityListSerializer, EighthAddSignupSerializer, EighthBlockDetailSerializer,
                           EighthBlockListSerializer, EighthScheduledActivitySerializer, EighthSignupSerializer, EighthToggleFavoriteSerializer)

logger = logging.getLogger(__name__)


class IsAuthenticatedOrClientCredentials(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool((request.user and request.user.is_authenticated and not request.user.is_restricted) or request.auth)


class EighthActivityList(generics.ListAPIView):
    queryset = EighthActivity.undeleted_objects.all().order_by("id")
    serializer_class = EighthActivityListSerializer
    permission_classes = (IsAuthenticatedOrClientCredentials,)


class EighthActivityDetail(generics.RetrieveAPIView):
    """API endpoint that shows details of an eighth activity."""

    queryset = EighthActivity.undeleted_objects.all().order_by("id")
    serializer_class = EighthActivityDetailSerializer
    permission_classes = (IsAuthenticatedOrClientCredentials,)


class BlockPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class EighthBlockList(generics.ListAPIView):
    """API endpoint that lists all eighth blocks."""

    serializer_class = EighthBlockListSerializer
    pagination_class = BlockPagination
    permission_classes = (IsAuthenticatedOrClientCredentials,)

    def is_valid_date(self, date_text):
        try:
            datetime.strptime(date_text, "%Y-%m-%d")
        except ValueError:
            return False
        return True

    def get_queryset(self):
        if "start_date" in self.request.GET:
            start_date = self.request.GET.get("start_date")
            if not self.is_valid_date(start_date):
                raise ValidationError("Invalid format for start_date.")

            return EighthBlock.objects.filter(date__gte=start_date).order_by("id")

        if "date" in self.request.GET:
            date = self.request.GET.get("date")
            if not self.is_valid_date(date):
                raise ValidationError("Invalid format for date.")
            return EighthBlock.objects.filter(date=date).order_by("id")

        return EighthBlock.objects.get_blocks_this_year()


class EighthBlockDetail(views.APIView):
    """API endpoint that shows details for an eighth block."""

    permission_classes = (IsAuthenticatedOrClientCredentials,)

    def get(self, request, pk):
        try:
            block = EighthBlock.objects.prefetch_related("eighthscheduledactivity_set").get(pk=pk)
        except EighthBlock.DoesNotExist:
            raise Http404

        serializer = EighthBlockDetailSerializer(block, context={"request": request})
        return Response(serializer.data)


class EighthUserSignupListAdd(generics.ListCreateAPIView):
    serializer_class = EighthAddSignupSerializer
    queryset = EighthSignup.objects.all().order_by("id")

    def is_valid_date(self, date_text):
        try:
            datetime.strptime(date_text, "%Y-%m-%d")
        except ValueError:
            return False
        return True

    def list(self, request, user_id=None):  # pylint: disable=arguments-differ
        if not user_id:
            user_id = request.user.id
        elif not get_user_model().objects.get(id=user_id).can_view_eighth:
            serialized = EighthSignupSerializer([], context={"request": request}, many=True)
            return Response(serialized.data)

        all_signups = EighthSignup.objects.filter(user_id=user_id).prefetch_related("scheduled_activity__block")

        if "date" in request.GET:
            date = self.request.GET.get("date")
            if not self.is_valid_date(date):
                raise ValidationError("Invalid format for date.")
            all_signups = all_signups.filter(scheduled_activity__block__date=date)
        elif "start_date" in request.GET:
            start_date = self.request.GET.get("start_date")
            if not self.is_valid_date(start_date):
                raise ValidationError("Invalid format for start_date.")
            all_signups = all_signups.filter(scheduled_activity__block__date__gte=start_date)
        else:
            all_signups = all_signups.filter(scheduled_activity__block__in=EighthBlock.objects.get_blocks_this_year())

        signups = all_signups.select_related("scheduled_activity__activity").order_by(
            "scheduled_activity__block__date", "scheduled_activity__block__block_letter"
        )

        serialized = EighthSignupSerializer(signups, context={"request": request}, many=True)

        return Response(serialized.data)

    def create(self, request, user_id=None):
        if user_id and not request.user.is_eighth_admin:
            raise PermissionDenied
        elif user_id:
            user = get_user_model().objects.get(id=user_id)
        else:
            user = request.user

        serializer = EighthAddSignupSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if (
            "activity" not in serializer.validated_data
            or "block" not in serializer.validated_data
            or serializer.validated_data.get("use_scheduled_activity", False)
        ):
            schactivity = serializer.validated_data["scheduled_activity"]
        else:
            schactivity = (
                EighthScheduledActivity.objects.filter(activity=serializer.validated_data["activity"])
                .filter(block=serializer.validated_data["block"])
                .get()
            )
        if "force" in serializer.validated_data:
            force = serializer.validated_data["force"]
        else:
            force = False

        if force and not request.user.is_eighth_admin:
            return Response({"error": "You are not an administrator."}, status=status.HTTP_400_BAD_REQUEST)

        schactivity.add_user(user, request, force=force)

        return Response(EighthActivityDetailSerializer(schactivity.activity, context={"request": request}).data, status=status.HTTP_201_CREATED)


class EighthUserFavoritesListToggle(generics.ListCreateAPIView):
    serializer_class = EighthToggleFavoriteSerializer
    queryset = EighthActivity.undeleted_objects.all()

    def get_queryset(self):
        user_id = self.request.user.id
        user = get_user_model().objects.get(id=user_id)
        return user.favorited_activity_set.all()

    def list(self, request):  # pylint: disable=arguments-differ
        serialized = EighthActivityListSerializer(self.get_queryset(), context={"request": request}, many=True)
        return Response(serialized.data)

    def create(self, request, user_id=None):
        if user_id:
            user = get_user_model().objects.get(id=user_id)
        else:
            user = request.user

        serializer = EighthToggleFavoriteSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        activity = serializer.validated_data["activity"]
        favorites = user.favorited_activity_set
        if activity in favorites.all():
            favorites.remove(activity)
        else:
            favorites.add(activity)
        return Response(EighthActivityDetailSerializer(activity, context={"request": request}).data, status=status.HTTP_201_CREATED)
        # except EighthActivity.DoesNotExist:
        #     return Response({"error": "The activity does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        # except Exception:
        #     return Response({"error": "An unknown error occurred"}, status=status.HTTP_400_BAD_REQUEST)


class EighthUserFavoritesAdd(generics.CreateAPIView):
    serializer_class = EighthActivityDetailSerializer
    queryset = EighthActivity.undeleted_objects.all()

    def get_queryset(self):
        user_id = self.request.user.id
        user = get_user_model().objects.get(id=user_id)
        return user.favorited_activity_set.all()

    def create(self, request, user_id=None):  # pylint: disable=arguments-differ
        if user_id:
            user = get_user_model().objects.get(id=user_id)
        else:
            user = request.user
        try:
            activity = EighthActivity.objects.get(id=request.data.get("id"))
            favorites = user.favorited_activity_set
            favorites.add(activity)
            return Response(EighthActivityDetailSerializer(activity, context={"request": request}).data, status=status.HTTP_201_CREATED)
        except EighthActivity.DoesNotExist:
            return Response({"error": "The activity does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "An unknown error occurred"}, status=status.HTTP_400_BAD_REQUEST)


class EighthUserFavoritesRemove(generics.ListCreateAPIView):
    serializer_class = EighthActivityListSerializer
    queryset = EighthActivity.undeleted_objects.all()

    def get_queryset(self):
        user_id = self.request.user.id
        user = get_user_model().objects.get(id=user_id)
        return user.favorited_activity_set.all()

    def list(self, request):  # pylint: disable=arguments-differ
        serialized = EighthActivityListSerializer(self.get_queryset(), context={"request": request}, many=True)

        return Response(serialized.data)

    def create(self, request, user_id=None):
        if user_id:
            user = get_user_model().objects.get(id=user_id)
        else:
            user = request.user

        try:
            activity = EighthActivity.objects.get(id=request.data.get("id"))
            favorites = user.favorited_activity_set
            favorites.remove(activity)
            return Response(EighthActivityDetailSerializer(activity, context={"request": request}).data, status=status.HTTP_201_CREATED)
        except EighthActivity.DoesNotExist:
            return Response({"error": "The activity does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "An unknown error occurred"}, status=status.HTTP_400_BAD_REQUEST)


class EighthScheduledActivitySignupList(views.APIView):
    """API endpoint that lists all signups for a certain scheduled activity."""

    def get(self, request, scheduled_activity_id):
        scheduled_activity = EighthScheduledActivity.objects.get(id=scheduled_activity_id)
        serializer = EighthScheduledActivitySerializer(scheduled_activity, context={"request": request})

        return Response(serializer.data)


class EighthSignupDetail(generics.RetrieveAPIView):
    """API endpoint that shows details of an eighth signup."""

    queryset = EighthSignup.objects.all()
    serializer_class = EighthSignupSerializer
