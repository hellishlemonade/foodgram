from django.db import models

from users.models import Profile


class Subscriber(models.Model):
    user = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        null=True,
        related_name='subscriber',
        verbose_name='Пользователь'
    )
    subscriptions = models.ManyToManyField(
        Profile, related_name='subscribers', verbose_name='Подписки'
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
