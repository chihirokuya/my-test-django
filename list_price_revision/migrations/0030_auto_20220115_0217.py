# Generated by Django 3.2.10 on 2022-01-14 17:17

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('list_price_revision', '0029_auto_20220106_0618'),
    ]

    operations = [
        migrations.AddField(
            model_name='usermodel',
            name='api_ok',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name='recordsmodel',
            name='date',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2022, 1, 15, 2, 17, 4, 446418), null=True),
        ),
    ]