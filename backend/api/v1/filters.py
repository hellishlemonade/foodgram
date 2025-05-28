import django_filters
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination

from recipes.models import Recipe, Tag


class IngredientFilter(SearchFilter):
    search_param = 'name'


class RecipesFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug'
    )
    is_favorited = django_filters.NumberFilter(
        method='filter_is_favorited',
        min_value=0,
        max_value=1
    )
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart',
        min_value=0,
        max_value=1
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags']

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value else queryset
        if int(value) == 1:
            return queryset.filter(favoritesrecipes__user=user)
        return queryset.exclude(favoritesrecipes__user=user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value else queryset
        if int(value) == 1:
            return queryset.filter(shoprecipes__user=user)
        return queryset.exclude(shoprecipes__user=user)


class CustomPagination(PageNumberPagination):
    max_page_size = 100
    page_size_query_param = 'limit'
