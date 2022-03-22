# Generated by Django 3.2.10 on 2022-03-20 19:51

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('list_price_revision', '0040_alter_recordsmodel_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asinmodel',
            name='variation_options',
            field=models.JSONField(default=[]),
        ),
        migrations.AlterField(
            model_name='recordsmodel',
            name='date',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2022, 3, 21, 4, 51, 27, 122130), null=True),
        ),
    ]
