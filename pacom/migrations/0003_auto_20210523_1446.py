# Generated by Django 3.1.6 on 2021-05-23 14:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pacom', '0002_pairsofoptionspark_quasi_level'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pairsofoptionspark',
            name='quasi_level',
            field=models.PositiveIntegerField(),
        ),
    ]
