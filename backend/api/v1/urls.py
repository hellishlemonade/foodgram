from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import MyUserViewSet

AUTH = 'auth'

router = DefaultRouter()
router.register('users', MyUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path(f'{AUTH}/', include('djoser.urls.authtoken')),
]
