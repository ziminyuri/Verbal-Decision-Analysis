# Generated by Django 3.1.6 on 2021-05-23 09:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modification', '0012_remove_modificationoption_already_fill_values'),
    ]

    operations = [
        migrations.AddField(
            model_name='criterionmodification',
            name='number',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
