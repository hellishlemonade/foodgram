from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import MyUserViewSet, MyUserCreateView

AUTH = 'auth'

router = DefaultRouter()
router.register('users', MyUserViewSet, basename='users')

urlpatterns = [
    path('users/', MyUserCreateView.as_view()),
    path('', include(router.urls)),
    path(f'{AUTH}/', include('djoser.urls.authtoken')),
]
