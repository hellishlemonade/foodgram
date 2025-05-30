from django.contrib import admin

from .models import Ingredient, Recipe, RecipeIngredient, Tag


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


class RecipeAdmin(admin.ModelAdmin):
    search_fields = ('name', 'author')
    list_filter = ('tags',)
    list_display = (
        'name',
        'author',
        'text',
        'ingredients',
        'tags',
        'is_favorite_count'
    )

    def is_favorite_count(self, obj):
        return obj.favoritesrecipes_set.count()


admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(RecipeIngredient)
