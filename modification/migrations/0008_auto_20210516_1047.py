# Generated by Django 3.1.6 on 2021-05-16 10:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('modification', '0007_modificationoption'),
    ]

    operations = [
        migrations.AlterField(
            model_name='modificationpairsofoptions',
            name='option_1',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='id_option_1_modification', to='modification.modificationoption'),
        ),
        migrations.AlterField(
            model_name='modificationpairsofoptions',
            name='option_2',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='id_option_2_modification', to='modification.modificationoption'),
        ),
    ]
