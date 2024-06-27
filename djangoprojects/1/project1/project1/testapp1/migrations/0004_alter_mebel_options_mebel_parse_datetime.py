# Generated by Django 4.2.7 on 2023-12-10 22:04

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('testapp1', '0003_alter_mebel_price'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='mebel',
            options={'ordering': ['price'], 'verbose_name': 'Мебель', 'verbose_name_plural': 'Мебель'},
        ),
        migrations.AddField(
            model_name='mebel',
            name='parse_datetime',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
