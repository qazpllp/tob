# Generated by Django 4.0.1 on 2022-02-07 15:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zone', '0003_alter_story_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='category',
            field=models.CharField(default='', max_length=30),
            preserve_default=False,
        ),
    ]
