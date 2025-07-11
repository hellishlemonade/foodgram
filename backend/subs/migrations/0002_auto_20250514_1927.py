# Generated by Django 3.2.3 on 2025-05-14 19:27

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('subs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriber',
            name='user',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subscriber', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='subscriber',
            name='subscriptions',
            field=models.ManyToManyField(related_name='subscribers', to=settings.AUTH_USER_MODEL),
        ),
    ]
