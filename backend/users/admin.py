from django.contrib import admin

from .models import Profile


class ProfileAdmin(admin.ModelAdmin):
    search_fields = ('username', 'email')


admin.site.register(Profile, ProfileAdmin)
