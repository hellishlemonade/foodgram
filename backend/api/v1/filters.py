import django_filters


from recipes.models import Recipe, Tag


class AuthorTagFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug'
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags']
