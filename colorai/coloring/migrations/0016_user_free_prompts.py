# Generated by Django 5.1.1 on 2025-07-04 10:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coloring', '0015_user_polar_customer_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='free_prompts',
            field=models.IntegerField(default=3),
        ),
    ]
