# Generated by Django 5.1.2 on 2024-10-12 18:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apiFaceId', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='face',
            name='encoding_path',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
