# Generated by Django 3.1.6 on 2021-05-12 09:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('snod', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='pairsofoptionstruesnod',
            name='in_result_and_not_comparable',
            field=models.BooleanField(default=False),
        ),
    ]
