from django.db import models

from users.models import Profile


class Subscriber(models.Model):
    user = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Пользователь'
    )
    subscriptions = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Подписки'
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('-id',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'subscriptions'],
                name='unique_subscription'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('subscriptions')),
                name='prevent_self_subscription'
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.subscriptions}'
