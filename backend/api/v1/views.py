from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.settings import api_settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .serializers import (
    MyUserCreateSerializer,
    MyUserSerializer,
    PasswordChangeSerializer,
    ImageSerializer,
)
from .permissions import IsUserOrAdminOrReadOnly, MePermission
from subs.models import Subscriber


User = get_user_model()


class MyUserCreateView(
    generics.ListCreateAPIView,
    generics.GenericAPIView
):
    queryset = User.objects.all()
    serializer_class = MyUserCreateSerializer
    permission_classes = [IsUserOrAdminOrReadOnly,]

    def list(self, request, *args, **kwargs):
        queryset = User.objects.all()
        paginator = api_settings.DEFAULT_PAGINATION_CLASS()
        page = paginator.paginate_queryset(queryset, request)
        serializer = MyUserSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class MyUserViewSet(viewsets.ModelViewSet):
    """
    Кастомный вьюсет для работы приложения users.

    Добавлены эндпоинты /me/, /set_password/, /me/avatar/.
    """
    queryset = User.objects.all()
    lookup_field = 'id'
    serializer_class = MyUserSerializer
    http_method_names = ('get', 'post', 'put', 'delete')
    permission_classes = [IsUserOrAdminOrReadOnly,]

    @action(detail=False, methods=['get'], permission_classes=[MePermission,])
    def me(self, request):
        user = request.user
        serializer = MyUserSerializer(user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated,],
        url_path='me/avatar'
    )
    def avatar(self, request):
        if request.method == 'PUT':
            user = request.user
            serializer = ImageSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(data=serializer.data)
        else:
            user = request.user
            user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'])
    def set_password(self, request):
        user = request.user
        if not user.check_password(request.data.get('current_password')):
            return Response(
                {"detail": "Uncorrect password"},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=['get'])
    def subscriptions(self, request):
        user = request.user
        subscriber = get_object_or_404(Subscriber, user=user)
        subscriptions = subscriber.subscriptions.all()
        serializer = MyUserSerializer(
            subscriptions, many=True, context={'request': request})
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='subscribe'
    )
    def get_subscriptions(self, request, id=None):
        user = request.user
        if request.method == 'POST':
            subscriber, _ = Subscriber.objects.get_or_create(
                user=user)
            if subscriber.subscriptions.filter(
                    id=self.get_object().id).exists():
                return Response(
                    {"detail": "Already subscribed"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if user == self.get_object():
                return Response(
                    {"detail": "You cant subscribe to yourself"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscriber.subscriptions.add(self.get_object())
            subscriber = subscriber.subscriptions.get(id=self.get_object().id)
            serializer = MyUserSerializer(
                subscriber, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            subscriber = get_object_or_404(Subscriber, user=user)
            if not subscriber.subscriptions.filter(
                    id=self.get_object().id).exists():
                return Response(
                    {"detail": "Not subscribed"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscriber.subscriptions.remove(self.get_object())
            return Response(
                {"detail": "Successfully unsubscribed"},
                status=status.HTTP_204_NO_CONTENT
            )
