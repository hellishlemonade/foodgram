from django.urls import path, include

AUTH = 'auth'

urlpatterns = [
    path('', include('djoser.urls')),
    path('{AUTH}/', include('djoser.urls.authtoken')),
]
