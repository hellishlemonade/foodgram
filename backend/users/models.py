from django.contrib.auth.models import AbstractUser
from django.db import models

from backend.constants import MAX_LENGTH_NAME


class Profile(AbstractUser):
    """
    Кастомная модель юзера, переопределяющая необязательные
    поля в обязательные.

    Добавлено поле для фотографии профиля.
    """
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    email = models.EmailField(
        'Email',
        unique=True,
        blank=False
    )

    first_name = models.CharField(
        'Имя',
        max_length=MAX_LENGTH_NAME,
        blank=False,
        null=False
    )

    last_name = models.CharField(
        'Фамилия',
        max_length=MAX_LENGTH_NAME,
        blank=False,
        null=False
    )

    avatar = models.ImageField(
        upload_to='users/',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return (
            f'Никнейм: {self.username}, email: {self.email}, '
            f'имя: {self.first_name}, фамилия: {self.last_name}'
        )
