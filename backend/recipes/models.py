from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Tag(models.Model):

    name = models.CharField(
        'Название', blank=False, unique=True, max_length=250)
    slug = models.SlugField('Слаг', blank=False, unique=True)

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Unit(models.Model):

    name = models.CharField('Название', blank=False, unique=True, max_length=50)

    class Meta:
        verbose_name = 'еденица измерения'
        verbose_name_plural = 'Еденицы измерения'

    def __str__(self):
        return self.name


class Ingredient(models.Model):

    name = models.CharField('Название', blank=False, max_length=250)
    measurement_unit = models.ForeignKey(
        Unit,
        related_name='ingredient',
        on_delete=models.CASCADE,
        verbose_name='Еденица измерения',
    )
    amount = models.PositiveSmallIntegerField('Количество', blank=False)

    class Meta:
        verbose_name = 'игредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):

    author = models.ForeignKey(
        User,
        blank=False,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Автор'
    )
    name = models.CharField('Название', blank=False, max_length=250)
    image = models.ImageField('Изображение', blank=False, upload_to='recipes/', null=True)
    text = models.TextField('Описание', blank=False)
    ingredients = models.ForeignKey(
        Ingredient,
        blank=False,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag, blank=False, related_name='recipe')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления', blank=False)

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name
