# Generated by Django 3.1.6 on 2021-03-21 07:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spbpu', '0013_auto_20210318_1228'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='model',
            name='id_winner_option_park',
        ),
        migrations.AddField(
            model_name='model',
            name='already_find_winner_PACOM',
            field=models.BooleanField(default=False),
        ),
    ]