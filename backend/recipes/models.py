from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator


User = get_user_model()


class Tag(models.Model):

    name = models.CharField(
        'Название', blank=False, unique=True, max_length=250
    )
    slug = models.SlugField('Слаг', blank=False, unique=True)

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):

    name = models.CharField('Название', blank=False, max_length=250)
    measurement_unit = models.CharField(
        'Еденица измерения',
        blank=False,
        max_length=100,
    )

    class Meta:
        verbose_name = 'игредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return str(self.name)


class Recipe(models.Model):

    author = models.ForeignKey(
        User,
        blank=False,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Автор'
    )
    name = models.CharField('Название', blank=False, max_length=256)
    image = models.ImageField(
        'Изображение', blank=False, upload_to='recipes/', null=True
    )
    text = models.TextField('Описание', blank=False)
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='ingredients',
        blank=False,
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        blank=False,
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[MinValueValidator(1)],
        blank=False
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeTag(models.Model):

    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, blank=False)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, blank=False)


class RecipeIngredient(models.Model):

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        blank=False,
        verbose_name='Рецепты'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        blank=False,
        verbose_name='Ингредиенты'
    )
    amount = models.PositiveSmallIntegerField(
        blank=False,
        validators=[MinValueValidator(1)],
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'рецепт и ингредиент'
        verbose_name_plural = 'Рецепты и ингредиенты'

    def __str__(self):
        return f'{self.recipe} - {self.ingredient}: {self.amount}'
