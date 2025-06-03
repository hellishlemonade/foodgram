import tempfile

from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from favorites.models import FavoritesRecipes
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from shopper.models import ShopRecipes
from subs.models import Subscriber

from .filters import CustomPagination, IngredientFilter, RecipesFilter
from .permissions import (
    IsUserOrAdminOrReadOnly,
    IsUserOrReadOnly,
    MePermission
)
from .serializers import (
    ImageSerializer,
    IngredientSerializer,
    ProfileSerializer,
    SubscriberSerializer,
    ReadRecipeSerializer,
    CreateRecipeSerializer,
    RecipeShortSerializer,
    TagSerializer,
    UserWithoutAuthorSerializer
)

User = get_user_model()
CONTEXT = {'fields_to_exclude': ['author']}


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
        subscriptions = user.subscriber.all().order_by('-id')
        page = self.paginate_queryset(subscriptions)
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
        if count_delete < 1:
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


# class RecipeViewSet(viewsets.ModelViewSet):

#     serializer_class = RecipeSerializer
#     lookup_field = 'id'
#     http_method_names = ('get', 'post', 'patch', 'delete')
#     permission_classes = [IsUserOrReadOnly, ]
#     filter_backends = (DjangoFilterBackend,)
#     pagination_class = CustomPagination
#     filterset_class = RecipesFilter

#     def get_queryset(self):
#         queryset = Recipe.objects.select_related('author').prefetch_related(
#             Prefetch('tags', queryset=Tag.objects.only('id', 'name', 'slug')),
#             Prefetch('ingredients', queryset=Ingredient.objects.only(
#                 'id', 'name', 'measurement_unit')
#             ),
#             Prefetch(
#                 'recipeingredient_set',
#                 queryset=RecipeIngredient.objects.select_related('ingredient')
#             )
#         ).order_by('-id')
#         return queryset

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         recipe = serializer.save(author=request.user)
#         return Response(
#             self.get_serializer(recipe).data,
#             status=status.HTTP_201_CREATED
#         )

#     @action(
#         detail=True,
#         methods=('get',),
#         url_path='get-link'
#     )
#     def shortlink(self, request, id=None):
#         recipe = get_object_or_404(Recipe, id=self.get_object().id)
#         url = reverse('recipes-detail', kwargs={'id': recipe.id})
#         return Response({'short-link': url})

#     @action(
#         detail=True,
#         methods=('post', 'delete'),
#         permission_classes=[IsAuthenticated],
#         url_path='favorite'
#     )
#     def favorite(self, request, id=None):
#         recipe = get_object_or_404(Recipe, id=self.get_object().id)
#         serializer = RecipeShortSerializer(recipe)
#         user = request.user
#         return add_or_delete_to_list(
#             request=request,
#             model=FavoritesRecipes,
#             user=user,
#             recipe=recipe,
#             serializer=serializer,
#             string='избранное'
#         )

#     @action(
#         detail=True,
#         methods=('post', 'delete'),
#         permission_classes=[IsAuthenticated]
#     )
#     def shopping_cart(self, request, id=None):
#         recipe = get_object_or_404(Recipe, id=self.get_object().id)
#         serializer = RecipeShortSerializer(recipe)
#         user = request.user
#         return add_or_delete_to_list(
#             request=request,
#             model=ShopRecipes,
#             user=user,
#             recipe=recipe,
#             serializer=serializer,
#             string='список покупок'
#         )

#     @action(
#         detail=False,
#         methods=('get',),
#         permission_classes=[IsAuthenticated]
#     )
#     def download_shopping_cart(self, request):
#         user = request.user
#         shop_list = ShopRecipes.objects.filter(user=user)
#         final_shop_list = {}
#         for recipe in shop_list:
#             recipe_ingredients = RecipeIngredient.objects.filter(
#                 recipe=recipe.recipes
#             )
#             for ing in recipe_ingredients:
#                 ingredient = ing.ingredient
#                 if final_shop_list.get(ingredient.name):
#                     amount, _ = final_shop_list[ingredient.name]
#                     result = amount + ing.amount
#                     final_shop_list[ingredient.name] = (
#                         result,
#                         ingredient.measurement_unit
#                     )
#                 else:
#                     final_shop_list[ingredient.name] = (
#                         ing.amount,
#                         ingredient.measurement_unit
#                     )
#         with tempfile.NamedTemporaryFile(
#             mode='w+', suffix='.txt', encoding='utf-8', delete=False
#         ) as temp_file:
#             for name, (amount, unit) in final_shop_list.items():
#                 temp_file.write(f"{name}: {amount} {unit}, ")
#             temp_file_path = temp_file.name
#             response = FileResponse(
#                 open(temp_file_path, 'rb'),
#                 content_type='text/plain',
#                 as_attachment=True,
#                 filename='shopping_list.txt'
#             )
#         with open(temp_file_path, 'rb') as f:
#             file_content = f.read()
#         response = Response(
#             file_content,
#             content_type='text/plain',
#             status=status.HTTP_200_OK
#         )
#         response[
#             'Content-Disposition'
#         ] = 'attachment; filename="shopping_list.txt"'
#         return response
