# Generated by Django 3.1.6 on 2021-05-15 09:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('modification', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='criterionmodification',
            name='model_m',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='modification.modelmodification'),
            preserve_default=False,
        ),
    ]