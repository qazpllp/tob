# Generated by Django 4.0.1 on 2022-02-22 12:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zone', '0006_story_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='story',
            name='text_html',
            field=models.FileField(default='', upload_to='story_text_html'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='story',
            name='text_pdf',
            field=models.FileField(default='', upload_to='story_text_pdf'),
            preserve_default=False,
        ),
    ]