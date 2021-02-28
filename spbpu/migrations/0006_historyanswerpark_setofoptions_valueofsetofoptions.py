# Generated by Django 3.1.6 on 2021-02-28 10:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('spbpu', '0005_auto_20210228_0858'),
    ]

    operations = [
        migrations.CreateModel(
            name='SetOfOptions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='spbpu.option')),
            ],
        ),
        migrations.CreateModel(
            name='ValueOfSetOfOptions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('set_option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='spbpu.setofoptions')),
                ('value', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='spbpu.value')),
            ],
        ),
        migrations.CreateModel(
            name='HistoryAnswerPARK',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='spbpu.model')),
                ('pair', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='spbpu.pairsofoptionspark')),
                ('set_option_1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='set_option_1', to='spbpu.setofoptions')),
                ('set_option_2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='set_option_2', to='spbpu.setofoptions')),
                ('winner_set', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='winner_set', to='spbpu.setofoptions')),
            ],
        ),
    ]
