# Generated by Django 3.1.6 on 2021-05-15 16:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('model', '0001_initial'),
        ('modification', '0002_criterionmodification_model_m'),
    ]

    operations = [
        migrations.AlterField(
            model_name='criterionmodification',
            name='criterion',
            field=models.ManyToManyField(blank=True, to='model.Criterion', verbose_name='Исходный критерий'),
        ),
        migrations.AlterField(
            model_name='criterionmodification',
            name='name',
            field=models.CharField(max_length=200, verbose_name='Название критерия'),
        ),
        migrations.CreateModel(
            name='ModificationValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.FloatField()),
                ('criterion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='modification.criterionmodification')),
                ('option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='model.option')),
            ],
        ),
    ]