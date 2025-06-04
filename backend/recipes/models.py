from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
import secrets

from backend.constants import (
    AMOUNT_MAX,
    AMOUNT_MIN,
    COOKING_TIME_MAX,
    COOKING_TIME_MIN,
    INGREDIENT_NAME_MAX_LENGTH,
    MEASUREMENT_UNIT_MAX_LENGTH,
    RECIPE_NAME_MAX_LENGTH,
    SHORT_LINK_MAX_SIZE,
    TAG_NAME_MAX_LENGTH,
    TAG_SLUG_MAX_LENGTH
)

User = get_user_model()


class Tag(models.Model):

    name = models.CharField(
        'Название', unique=True, max_length=TAG_NAME_MAX_LENGTH
    )
    slug = models.SlugField(
        'Слаг', unique=True, max_length=TAG_SLUG_MAX_LENGTH
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.slug


class Ingredient(models.Model):

    name = models.CharField('Название', max_length=INGREDIENT_NAME_MAX_LENGTH)
    measurement_unit = models.CharField(
        'Еденица измерения',
        max_length=MEASUREMENT_UNIT_MAX_LENGTH,
    )

    class Meta:
        verbose_name = 'игредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('-id',)
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='ingredient_unique'
            )
        ]

    def __str__(self):
        return f'{self.name} - {self.measurement_unit}'


class Recipe(models.Model):

    author = models.ForeignKey(
        User,
        blank=False,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Автор'
    )
    name = models.CharField('Название', max_length=RECIPE_NAME_MAX_LENGTH)
    image = models.ImageField(
        'Изображение', blank=False, upload_to='recipes/', null=True
    )
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='ingredients',
    )
    tags = models.ManyToManyField(Tag)
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=(
            MinValueValidator(
                COOKING_TIME_MIN,
                f'Вы не можете ввести значение меньше {COOKING_TIME_MIN} мин.'
            ),
            MaxValueValidator(
                COOKING_TIME_MAX,
                f'Вы не можете ввести значение больше {COOKING_TIME_MAX} мин.'
            )
        )
    )
    short_url = models.CharField(
        max_length=SHORT_LINK_MAX_SIZE, unique=True, null=True
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-id',)

    def __str__(self):
        return self.name

    def generate_short_url(self):
        alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
        while True:
            short_url = ''.join(secrets.choice(alphabet) for _ in range(6))
            if not Recipe.objects.filter(short_url=short_url).exists():
                return short_url

    def save(self, *args, **kwargs):
        if not self.short_url:
            self.short_url = self.generate_short_url()
        super().save(*args, **kwargs)

    def get_short_url(self, request):
        path = reverse(
            'recipe-short-link', kwargs={'short_link': self.short_url}
        )
        return request.build_absolute_uri(path)

    def get_absolute_url(self):
        return reverse('recipes-detail', kwargs={'id': self.id})


class RecipeIngredient(models.Model):

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепты',
        related_name='ingredient_links'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиенты',
        related_name='recipe_links'
    )
    amount = models.PositiveSmallIntegerField(
        blank=False,
        validators=(
            MinValueValidator(
                AMOUNT_MIN,
                f'Вы не можете указать количестов меньше {AMOUNT_MIN}'
            ),
            MaxValueValidator(
                AMOUNT_MAX,
                f'Вы не можете указать количество больше {AMOUNT_MAX}'
            )
        ),
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'рецепт и ингредиент'
        verbose_name_plural = 'Рецепты и ингредиенты'
        ordering = ('-id',)
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='recipe_ingredient_unique'
            )
        ]

    def __str__(self):
        return f'{self.recipe} - {self.ingredient}: {self.amount}'
