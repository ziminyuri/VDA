# Generated by Django 3.1.6 on 2021-03-25 17:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spbpu', '0016_auto_20210321_0836'),
    ]

    operations = [
        migrations.AddField(
            model_name='pairsofoptionspark',
            name='flag_winner_option',
            field=models.IntegerField(default=-1),
        ),
    ]
