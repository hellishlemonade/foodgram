from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (IngredientViewSet, MyUserCreateView, MyUserViewSet,
                    RecipeViewSet, TagViewSet)

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
