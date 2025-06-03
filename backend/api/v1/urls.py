from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    IngredientViewSet,
    ProfileUserViewSet,
    TagViewSet
)

AUTH = 'auth'

router = DefaultRouter()
router.register('users', ProfileUserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
# router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path(f'{AUTH}/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
