from django.db import models

from users.models import Profile


class Subscriber(models.Model):
    user = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        null=True,
        related_name='subscriber'
    )
    subscriptions = models.ManyToManyField(Profile, related_name='subscribers')
