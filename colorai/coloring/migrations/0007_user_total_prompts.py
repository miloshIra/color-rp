# Generated by Django 5.1.1 on 2025-02-23 11:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coloring', '0006_delete_subscription_user_billing_period_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='total_prompts',
            field=models.IntegerField(default=0),
        ),
    ]
