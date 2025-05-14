from rest_framework import viewsets, status
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from rest_framework.response import Response

from .serializers import (
    MyUserCreateSerializer,
    PasswordChangeSerializer,
    Base64ImageField,
    ImageSerializer
)
from .permissions import IsUserOrAdminOrReadOnly


User = get_user_model()


class MyUserViewSet(viewsets.ModelViewSet):
    """
    Кастомный вьюсет для работы приложения users.

    Добавлены эндпоинты /me/, /set_password/, /me/avatar/.
    """
    queryset = User.objects.all()
    lookup_field = 'id'
    serializer_class = MyUserCreateSerializer
    http_method_names = ('get', 'post', 'put', 'delete')
    permission_classes = [IsUserOrAdminOrReadOnly,]

    @action(detail=False, methods=['get'])
    def me(self, request):
        user = request.user
        serializer = MyUserCreateSerializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def avatar(self, request):
        user = request.user
        serializer = ImageSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data)

    @action(detail=False, methods=['post'])
    def set_password(self, request):
        user = request.user
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
