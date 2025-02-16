from django.db.models.signals import post_save
from django.dispatch import receiver

from colorai import settings
from coloring import models as models
from coloring.utils import discord_prompt_stats, discord_user_stats


@receiver(post_save, sender=models.Prompt)
def after_prompt_saved(sender, instance, created, **kwargs):
    if created:
        prompt_count = models.Prompt.objects.all().count()
        estimated_storage_size = prompt_count * 280 / 1024

        number = str(estimated_storage_size).split(".")[0]

        decimal = str(estimated_storage_size).split(".")[1]
        size = number + "." + decimal[:2] + "MB"
        bill = str(prompt_count * 0.0036) + " $"

        discord_prompt_stats(
            discord_webhook_url=settings.DISCORD_STATS_WEBHOOK,
            prompts=prompt_count,
            size=size,
            bill=bill,
            user=instance.user.email,
        )


@receiver(post_save, sender=models.User)
def after_prompt_saved(sender, instance, created, **kwargs):
    if created:
        users_count = models.User.objects.all().count()
        discord_user_stats(
            discord_webhook_url=settings.DISCORD_STATS_WEBHOOK, number=users_count
        )
