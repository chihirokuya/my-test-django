# Generated by Django 3.2.10 on 2022-03-20 20:12

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('list_price_revision', '0041_auto_20220321_0451'),
    ]

    operations = [
        migrations.AddField(
            model_name='asinmodel',
            name='base_name',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='recordsmodel',
            name='date',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2022, 3, 21, 5, 12, 32, 901854), null=True),
        ),
    ]
