# Generated by Django 3.1.6 on 2021-03-21 08:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('spbpu', '0014_auto_20210321_0743'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoryAnswerPACOM',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.TextField(max_length=1000)),
                ('answer', models.CharField(max_length=255)),
                ('id_model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='spbpu.model')),
                ('pair', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pair_pacom', to='spbpu.pairsofoptionspark')),
            ],
        ),
    ]
