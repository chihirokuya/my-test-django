# Generated by Django 3.2.10 on 2022-03-07 15:50

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('list_price_revision', '0013_alter_recordsmodel_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recordsmodel',
            name='date',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2022, 3, 8, 0, 50, 7, 829722), null=True),
        ),
    ]
