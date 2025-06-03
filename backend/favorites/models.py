from django.contrib.auth import get_user_model
from django.db import models

from recipes.models import Recipe

User = get_user_model()


class FavoritesRecipes(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipes = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorites'
    )

    class Meta:
        verbose_name = 'избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        ordering = ('-id',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipes'),
                name='favorites_recipes_unique'
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.recipes.name}'
