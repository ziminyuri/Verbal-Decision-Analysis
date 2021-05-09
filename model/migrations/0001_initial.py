# Generated by Django 3.1.6 on 2021-05-08 20:05

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Criterion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('name', models.CharField(max_length=200)),
                ('direction', models.BooleanField()),
                ('max', models.FloatField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Model',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_demo', models.BooleanField()),
                ('name', models.CharField(max_length=255)),
                ('id_winner_option_many', models.IntegerField(null=True)),
                ('id_winner_option_shnur', models.IntegerField(null=True)),
                ('time_shnur', models.CharField(max_length=255)),
                ('time_answer_shnur', models.CharField(max_length=255)),
                ('time_many', models.CharField(max_length=255)),
                ('already_find_winner_PACOM', models.BooleanField(default=False)),
                ('time_answer_pacom', models.CharField(max_length=255)),
                ('number_of_questions_pacom', models.IntegerField(default=0)),
                ('number_of_pairs', models.IntegerField(default=0)),
                ('number_of_incomparable', models.IntegerField(default=0)),
                ('already_find_winner_SNOD', models.BooleanField(default=False)),
                ('time_answer_snod', models.CharField(max_length=255)),
                ('number_of_questions_snod', models.IntegerField(default=0)),
                ('number_of_pairs_snod', models.IntegerField(default=0)),
                ('number_of_incomparable_snod', models.IntegerField(default=0)),
                ('number_repeated_questions_snod', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Option',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('number', models.IntegerField()),
                ('quasi_order_pacom', models.IntegerField(default=0)),
                ('quasi_order_original_snod', models.IntegerField(default=0)),
                ('id_model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='model.model')),
            ],
        ),
        migrations.CreateModel(
            name='SettingsOrigianlSNOD',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('auto_mode', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='SettingsPACOM',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('auto_mode', models.BooleanField(default=False)),
                ('larichev_question', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Value',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.FloatField()),
                ('id_criterion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='model.criterion')),
                ('id_option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='model.option')),
            ],
        ),
        migrations.AddField(
            model_name='model',
            name='id_settings_original_snod',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='model.settingsorigianlsnod'),
        ),
        migrations.AddField(
            model_name='model',
            name='id_settings_pacom',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='model.settingspacom'),
        ),
        migrations.AddField(
            model_name='model',
            name='id_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='criterion',
            name='id_model',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='model.model'),
        ),
    ]
