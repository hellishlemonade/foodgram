import tempfile

from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Sum, Count
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from favorites.models import FavoritesRecipes
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from shopper.models import ShopRecipes
from subs.models import Subscriber

from .filters import IngredientFilter, RecipesFilter
from .paginations import CustomPagination
from .permissions import IsUserOrReadOnly
from .serializers import (
    CreateRecipeSerializer,
    FavoritesRecipeSerializer,
    ImageSerializer,
    IngredientSerializer,
    ProfileSerializer,
    ReadRecipeSerializer,
    ShopperRecipeSerializer,
    SubscriberSerializer,
    TagSerializer,
    UserWithoutAuthorSerializer
)

User = get_user_model()


class ProfileUserViewSet(UserViewSet):
    """
    Кастомный вьюсет для работы приложения users.

    Добавлены эндпоинты /me/, /set_password/, /me/avatar/.
    """
    queryset = User.objects.all()
    lookup_field = 'id'
    serializer_class = ProfileSerializer
    http_method_names = ('get', 'post', 'put', 'delete')
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPagination

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(
        detail=False,
        methods=('put',),
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar'
    )
    def avatar(self, request):
        user = request.user
        serializer = ImageSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request, *args, **kwargs):
        user = self.request.user
        user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        pagination_class=CustomPagination
    )
    def subscriptions(self, request):
        user = request.user
        subscriptions = user.subscriber.all(
        ).order_by('-id').values('subscriptions__username')
        subs = User.objects.filter(username__in=subscriptions)
        page = self.paginate_queryset(subs)
        serializer = UserWithoutAuthorSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        url_path='subscribe'
    )
    def get_subscriptions(self, request, id=None):
        subscription = get_object_or_404(User, id=id)
        serializer = SubscriberSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, subscriptions=subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @get_subscriptions.mapping.delete
    def delete_subscriptions(self, request, *args, **kwargs):
        count_delete, _ = Subscriber.objects.filter(
            user=request.user, subscriptions=self.get_object()
        ).delete()
        if not count_delete:
            return Response(
                {'detail': 'Not subscribed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ModelViewSet):

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = 'id'
    http_method_names = ('get')
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    lookup_field = 'id'
    http_method_names = ('get')
    pagination_class = None
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)


def recipe_short_link(request, short_link):
    recipe = get_object_or_404(Recipe, short_url=short_link)
    return HttpResponseRedirect(redirect_to=recipe.get_absolute_url())


class RecipeViewSet(viewsets.ModelViewSet):

    lookup_field = 'id'
    http_method_names = ('get', 'post', 'patch', 'delete')
    permission_classes = (IsUserOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    pagination_class = CustomPagination
    filterset_class = RecipesFilter

    @staticmethod
    def add_to(serializer_class, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        serializer = serializer_class(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, recipes=recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def delete_from(model, request, self):
        count_delete, _ = model.objects.filter(
            user=request.user, recipes=self.get_object()).delete()
        if not count_delete:
            return Response(
                {'detail': 'Not subscribed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve', 'get-link'):
            return ReadRecipeSerializer
        return CreateRecipeSerializer

    def get_queryset(self):
        queryset = Recipe.objects.select_related('author').prefetch_related(
            Prefetch('tags', queryset=Tag.objects.only('id', 'name', 'slug')),
            Prefetch('ingredients', queryset=Ingredient.objects.only(
                'id', 'name', 'measurement_unit')
            ),
            Prefetch(
                'ingredient_links',
                queryset=RecipeIngredient.objects.select_related('ingredient')
            )
        ).order_by('-id')
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=('get',),
        url_path='get-link'
    )
    def shortlink(self, request, id=None):
        recipe = get_object_or_404(Recipe, id=id)
        url = recipe.get_short_url(request)
        return Response({'short-link': url})

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        url_path='favorite'
    )
    def favorite(self, request, id=None):
        return self.add_to(FavoritesRecipeSerializer, request, id)

    @favorite.mapping.delete
    def delete_favorite(self, request, *args, **kwargs):
        return self.delete_from(FavoritesRecipes, request, self)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, id=None):
        return self.add_to(ShopperRecipeSerializer, request, id)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, *args, **kwargs):
        return self.delete_from(ShopRecipes, request, self)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        ingredients = (
            Ingredient.objects.filter(
                ingredients__in_shopping_cart__user=request.user)
            .values('name', 'measurement_unit')
            .annotate(sum=Sum('recipe_links__amount'))
        )
        shopping_list_as_str = '\n'.join(
            f'{ingredient["name"]} - {ingredient["sum"]} '
            f'({ingredient["measurement_unit"]})'
            for ingredient in ingredients
        )
        return HttpResponse(shopping_list_as_str, content_type='text/plain')
