# Generated by Django 3.1.6 on 2021-05-17 08:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('modification', '0011_modificationoption_already_fill_values'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='modificationoption',
            name='already_fill_values',
        ),
    ]
