from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

MAX_LENGTH_USERNAME = 150
MAX_LENGTH_NAME = 150


class Profile(AbstractUser):
    """
    Кастомная модель юзера, переопределяющая необязательные
    поля в обязательные.

    Добавлено поле для фотографии профиля.
    """
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    username = models.CharField(
        'Никнейм',
        max_length=MAX_LENGTH_USERNAME,
        unique=True,
        validators=[UnicodeUsernameValidator()]
    )

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
