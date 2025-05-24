from django.contrib import admin

from .models import Tag, Recipe, Ingredient, RecipeIngredient


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')


admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(RecipeIngredient)
