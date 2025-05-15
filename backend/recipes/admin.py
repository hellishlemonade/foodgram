from django.contrib import admin

from .models import Tag, Unit, Recipe, Ingredient


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


admin.site.register(Tag, TagAdmin)
admin.site.register(Unit)
admin.site.register(Recipe)
admin.site.register(Ingredient)
