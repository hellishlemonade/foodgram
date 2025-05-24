from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    MyUserViewSet,
    MyUserCreateView,
    TagViewSet,
    IngredientViewSet,
    RecipeViewSet,
)

AUTH = 'auth'

router = DefaultRouter()
router.register('users', MyUserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path(f'{AUTH}/', include('djoser.urls.authtoken')),
    path('users/', MyUserCreateView.as_view()),
    path('', include(router.urls)),
]
