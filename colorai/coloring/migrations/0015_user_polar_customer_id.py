# Generated by Django 5.1.1 on 2025-06-29 11:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coloring', '0014_alter_user_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='polar_customer_id',
            field=models.CharField(blank=True, null=True),
        ),
    ]
