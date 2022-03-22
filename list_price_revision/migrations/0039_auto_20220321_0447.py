# Generated by Django 3.2.10 on 2022-03-20 19:47

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('list_price_revision', '0038_auto_20220321_0446'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asinmodel',
            name='variation_options',
            field=models.JSONField(blank=True, default=[], null=True),
        ),
        migrations.AlterField(
            model_name='recordsmodel',
            name='date',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2022, 3, 21, 4, 47, 44, 590870), null=True),
        ),
    ]