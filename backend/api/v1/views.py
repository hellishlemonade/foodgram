import tempfile

from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
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
    MyUserCreateSerializer,
    MyUserSerializer,
    PasswordChangeSerializer,
    RecipeSerializer,
    RecipeShortSerializer,
    TagSerializer,
    UserWithoutAuthorSerializer
)

User = get_user_model()
CONTEXT = {'fields_to_exclude': ['author']}


def add_or_delete_to_list(request, model, user, recipe, serializer, string):
    if request.method == 'POST':
        if model.objects.filter(
            user=user, recipes=recipe
        ).exists():
            return Response(
                {'detail': f'Рецепт уже добавлен в {string}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        model.objects.create(user=user, recipes=recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    try:
        favorite_list = model.objects.get(user=user, recipes=recipe)
    except model.DoesNotExist:
        return Response(
            {'detail': 'Объект не найден'},
            status=status.HTTP_400_BAD_REQUEST
        )
    favorite_list.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


class MyUserCreateView(
    generics.ListCreateAPIView,
    generics.GenericAPIView
):
    queryset = User.objects.all()
    serializer_class = MyUserCreateSerializer
    permission_classes = [IsUserOrAdminOrReadOnly, ]

    def list(self, request, *args, **kwargs):
        queryset = User.objects.all()
        paginator = LimitOffsetPagination()
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
    permission_classes = [IsUserOrAdminOrReadOnly, ]

    @action(detail=False, methods=['get'], permission_classes=[MePermission, ])
    def me(self, request):
        user = request.user
        serializer = MyUserSerializer(user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated, ],
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
                {'detail': 'Uncorrect password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated, ],
        pagination_class=CustomPagination
    )
    def subscriptions(self, request):
        user = request.user
        subscriber = get_object_or_404(Subscriber, user=user)
        subscriptions = subscriber.subscriptions.all().order_by('id')
        page = self.paginate_queryset(subscriptions)
        CONTEXT['request'] = request
        if page is not None:
            serializer = UserWithoutAuthorSerializer(
                page,
                many=True,
                context=CONTEXT
            )
            return self.get_paginated_response(serializer.data)
        serializer = MyUserSerializer(
            subscriptions, many=True, context=CONTEXT
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='subscribe'
    )
    def get_subscriptions(self, request, id=None):
        user = request.user
        target_user = self.get_object()
        if request.method == 'POST':
            subscriber, _ = Subscriber.objects.get_or_create(
                user=user)
            if subscriber.subscriptions.filter(
                    id=target_user.id).exists():
                return Response(
                    {'detail': 'Already subscribed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if user == target_user:
                return Response(
                    {'detail': 'You cant subscribe to yourself'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscriber.subscriptions.add(target_user)
            subscriber = subscriber.subscriptions.get(id=target_user.id)
            CONTEXT['request'] = request
            serializer = UserWithoutAuthorSerializer(
                subscriber, context=CONTEXT)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            try:
                subscriber = Subscriber.objects.get(user=user)
            except Subscriber.DoesNotExist:
                return Response(
                    {'detail': 'Not subscribed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not subscriber.subscriptions.filter(
                    id=target_user.id).exists():
                return Response(
                    {'detail': 'Not subscribed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscriber.subscriptions.remove(target_user)
            return Response(
                {'detail': 'Successfully unsubscribed'},
                status=status.HTTP_204_NO_CONTENT
            )


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


class RecipeViewSet(viewsets.ModelViewSet):

    serializer_class = RecipeSerializer
    lookup_field = 'id'
    http_method_names = ('get', 'post', 'patch', 'delete')
    permission_classes = [IsUserOrReadOnly, ]
    filter_backends = (DjangoFilterBackend,)
    pagination_class = LimitOffsetPagination
    filterset_class = RecipesFilter

    def get_queryset(self):
        queryset = Recipe.objects.select_related('author').prefetch_related(
            Prefetch('tags', queryset=Tag.objects.only('id', 'name', 'slug')),
            Prefetch('ingredients', queryset=Ingredient.objects.only(
                'id', 'name', 'measurement_unit')
            ),
            Prefetch(
                'recipeingredient_set',
                queryset=RecipeIngredient.objects.select_related('ingredient')
            )
        ).order_by('-id')
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save(author=request.user)
        return Response(
            self.get_serializer(recipe).data,
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=True,
        methods=('get',),
        url_path='get-link'
    )
    def shortlink(self, request, id=None):
        recipe = get_object_or_404(Recipe, id=self.get_object().id)
        url = reverse('recipes-detail', kwargs={'id': recipe.id})
        return Response({'short-link': url})

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=[IsAuthenticated],
        url_path='favorite'
    )
    def favorite(self, request, id=None):
        recipe = get_object_or_404(Recipe, id=self.get_object().id)
        serializer = RecipeShortSerializer(recipe)
        user = request.user
        return add_or_delete_to_list(
            request=request,
            model=FavoritesRecipes,
            user=user,
            recipe=recipe,
            serializer=serializer,
            string='избранное'
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, id=None):
        recipe = get_object_or_404(Recipe, id=self.get_object().id)
        serializer = RecipeShortSerializer(recipe)
        user = request.user
        return add_or_delete_to_list(
            request=request,
            model=ShopRecipes,
            user=user,
            recipe=recipe,
            serializer=serializer,
            string='список покупок'
        )

    @action(
        detail=False,
        methods=('get',),
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        shop_list = ShopRecipes.objects.filter(user=user)
        final_shop_list = {}
        for recipe in shop_list:
            recipe_ingredients = RecipeIngredient.objects.filter(
                recipe=recipe.recipes
            )
            for ing in recipe_ingredients:
                ingredient = ing.ingredient
                if final_shop_list.get(ingredient.name):
                    amount, _ = final_shop_list[ingredient.name]
                    result = amount + ing.amount
                    final_shop_list[ingredient.name] = (
                        result,
                        ingredient.measurement_unit
                    )
                else:
                    final_shop_list[ingredient.name] = (
                        ing.amount,
                        ingredient.measurement_unit
                    )
        with tempfile.NamedTemporaryFile(
            mode='w+', suffix='.txt', encoding='utf-8', delete=False
        ) as temp_file:
            for name, (amount, unit) in final_shop_list.items():
                temp_file.write(f"{name}: {amount} {unit}, ")
            temp_file_path = temp_file.name
            response = FileResponse(
                open(temp_file_path, 'rb'),
                content_type='text/plain',
                as_attachment=True,
                filename='shopping_list.txt'
            )
        with open(temp_file_path, 'rb') as f:
            file_content = f.read()
        response = Response(
            file_content,
            content_type='text/plain',
            status=status.HTTP_200_OK
        )
        response[
            'Content-Disposition'
        ] = 'attachment; filename="shopping_list.txt"'
        return response
