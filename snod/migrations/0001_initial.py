# Generated by Django 3.1.6 on 2021-05-13 12:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('model', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PairsOfOptionsTrueSNOD',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('already_find_winner', models.BooleanField(default=False)),
                ('is_not_comparable', models.BooleanField(default=False)),
                ('flag_winner_option', models.IntegerField(default=-1)),
                ('flag_not_compared', models.BooleanField(default=True)),
                ('in_result_and_not_comparable', models.BooleanField(default=False)),
                ('id_model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='model.model')),
                ('id_option_1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='id_option_1_true_snod', to='model.option')),
                ('id_option_2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='id_option_2_true_snod', to='model.option')),
            ],
        ),
        migrations.CreateModel(
            name='PairsOfOptions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='model.model')),
                ('id_option_1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='id_option_1', to='model.option')),
                ('id_option_2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='id_option_2', to='model.option')),
                ('winner_option', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='winner_option', to='model.option')),
                ('winner_option_many', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='winner_option_many', to='model.option')),
            ],
        ),
        migrations.CreateModel(
            name='HistoryAnswerTrueSNOD',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.TextField(max_length=1000)),
                ('answer', models.CharField(max_length=255)),
                ('id_model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='model.model')),
                ('pair', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pair_true_snod', to='snod.pairsofoptionstruesnod')),
            ],
        ),
        migrations.CreateModel(
            name='HistoryAnswer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.TextField(max_length=1000)),
                ('answer', models.CharField(max_length=255)),
                ('id_model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='model.model')),
                ('pair', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pair', to='snod.pairsofoptions')),
            ],
        ),
    ]
