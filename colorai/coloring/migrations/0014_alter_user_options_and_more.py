# Generated by Django 5.1.1 on 2025-06-14 09:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('coloring', '0013_prompt_visitor'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={},
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['supabase_id'], name='coloring_us_supabas_6e978a_idx'),
        ),
    ]
