# Generated by Django 3.1.6 on 2021-05-16 08:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modification', '0003_auto_20210515_1622'),
    ]

    operations = [
        migrations.AddField(
            model_name='criterionmodification',
            name='direction',
            field=models.BooleanField(default=True),
        ),
    ]
