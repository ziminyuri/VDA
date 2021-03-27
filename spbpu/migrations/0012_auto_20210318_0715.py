# Generated by Django 3.1.6 on 2021-03-18 07:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spbpu', '0011_winneroptionspacom'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pairsofoptionspark',
            name='winner_option',
        ),
        migrations.AddField(
            model_name='pairsofoptionspark',
            name='winners_option',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pacom_winners_option', to='spbpu.winneroptionspacom'),
        ),
    ]
