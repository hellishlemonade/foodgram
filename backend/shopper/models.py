from django.contrib.auth import get_user_model
from django.db import models

from recipes.models import Recipe

User = get_user_model()


class ShopRecipes(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipes = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return f'{self.user} - {self.recipes.name}'
