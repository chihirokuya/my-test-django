# Generated by Django 3.2.10 on 2022-03-08 19:09

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('list_price_revision', '0031_alter_recordsmodel_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recordsmodel',
            name='date',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2022, 3, 9, 4, 9, 17, 158562), null=True),
        ),
    ]