# Generated by Django 3.1.6 on 2021-05-23 14:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('model', '0002_auto_20210517_0623'),
    ]

    operations = [
        migrations.AddField(
            model_name='model',
            name='quasi_max_order_pacom',
            field=models.IntegerField(default=0),
        ),
    ]