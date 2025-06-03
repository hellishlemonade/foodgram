from django.contrib import admin

from .models import Ingredient, Recipe, RecipeIngredient, Tag


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


class RecipeIngredientInLine(admin.StackedInline):
    model = RecipeIngredient
    extra = 0
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeIngredientInLine,)
    search_fields = ('name', 'author__username')
    filter_horizontal = ('tags', 'ingredients')
    list_filter = ('tags',)
    list_display = (
        'name',
        'author',
        'text',
        'is_favorite_count'
    )

    def is_favorite_count(self, obj):
        return obj.favorites.count() if hasattr(obj, 'favorites') else 0
    is_favorite_count.short_description = 'В избранном'


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(RecipeIngredient)
admin.site.register(Recipe, RecipeAdmin)
