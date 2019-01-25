# -*- coding: utf-8 -*-

import logging

from django.http import Http404

from intranet.apps.users.models import User

from rest_framework import generics, status, views, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from ..models import (EighthActivity, EighthBlock, EighthScheduledActivity, EighthSignup)
from ..serializers import (EighthActivityDetailSerializer, EighthActivityListSerializer, EighthAddSignupSerializer, EighthBlockDetailSerializer,
                           EighthBlockListSerializer, EighthScheduledActivitySerializer, EighthSignupSerializer, EighthToggleFavoriteSerializer)

logger = logging.getLogger(__name__)


class IsAuthenticatedOrClientCredentials(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated or request.auth


class EighthActivityList(generics.ListAPIView):
    queryset = EighthActivity.undeleted_objects.all().order_by('id')
    serializer_class = EighthActivityListSerializer
    permission_classes = (IsAuthenticatedOrClientCredentials,)


class EighthActivityDetail(generics.RetrieveAPIView):
    """API endpoint that shows details of an eighth activity."""
    queryset = EighthActivity.undeleted_objects.all().order_by('id')
    serializer_class = EighthActivityDetailSerializer
    permission_classes = (IsAuthenticatedOrClientCredentials,)


class BlockPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class EighthBlockList(generics.ListAPIView):
    """API endpoint that lists all eighth blocks."""
    serializer_class = EighthBlockListSerializer
    pagination_class = BlockPagination
    permission_classes = (IsAuthenticatedOrClientCredentials,)

    def get_queryset(self):
        # get_current_blocks() actually returns a list, which you
        # can't .filter() on
        queryset = EighthBlock.objects.get_current_blocks()
        blk_ids = [b.id for b in queryset]

        if "start_date" in self.request.GET:
            return EighthBlock.objects.filter(id__in=blk_ids, date__gte=self.request.GET.get("start_date")).order_by('id')

        if "date" in self.request.GET:
            return EighthBlock.objects.filter(id__in=blk_ids, date=self.request.GET.get("date")).order_by('id')

        return queryset


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
    queryset = EighthSignup.objects.all().order_by('id')

    def list(self, request, user_id=None):
        if not user_id:
            user_id = request.user.id
        elif not User.objects.get(id=user_id).can_view_eighth:
            serialized = EighthSignupSerializer([], context={"request": request}, many=True)
            return Response(serialized.data)

        signups = EighthSignup.objects.filter(
            user_id=user_id).prefetch_related("scheduled_activity__block").select_related("scheduled_activity__activity").order_by(
                "scheduled_activity__block__date", "scheduled_activity__block__block_letter")

        serialized = EighthSignupSerializer(signups, context={"request": request}, many=True)

        return Response(serialized.data)

    def create(self, request, user_id=None):
        if user_id:
            user = User.objects.get(id=user_id)
        else:
            user = request.user

        serializer = EighthAddSignupSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if "activity" not in serializer.validated_data or "block" not in serializer.validated_data or serializer.validated_data.get(
                "use_scheduled_activity", False):
            schactivity = serializer.validated_data["scheduled_activity"]
        else:
            schactivity = EighthScheduledActivity.objects.filter(activity=serializer.validated_data["activity"]).filter(
                block=serializer.validated_data["block"]).get()
        if 'force' in serializer.validated_data:
            force = serializer.validated_data['force']
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
        user = User.objects.get(id=user_id)
        return user.favorited_activity_set.all()

    def list(self, request):
        serialized = EighthActivityListSerializer(self.get_queryset(), context={"request": request}, many=True)
        return Response(serialized.data)

    def create(self, request, user_id=None):
        if user_id:
            user = User.objects.get(id=user_id)
        else:
            user = request.user

        serializer = EighthToggleFavoriteSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        activity = serializer.validated_data['activity']
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
        user = User.objects.get(id=user_id)
        return user.favorited_activity_set.all()

    def create(self, request, user_id=None):
        if user_id:
            user = User.objects.get(id=user_id)
        else:
            user = request.user
        try:
            activity = EighthActivity.objects.get(id=request.data.get('id'))
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
        user = User.objects.get(id=user_id)
        return user.favorited_activity_set.all()

    def list(self, request):
        serialized = EighthActivityListSerializer(self.get_queryset(), context={"request": request}, many=True)

        return Response(serialized.data)

    def create(self, request, user_id=None):
        if user_id:
            user = User.objects.get(id=user_id)
        else:
            user = request.user

        try:
            activity = EighthActivity.objects.get(id=request.data.get('id'))
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
