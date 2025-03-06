import json
import traceback
from datetime import datetime

import requests
from rest_framework import status

from colorai import settings
from coloring.utils import discord_alert


class DiscordAlertException(Exception):

    def __init__(self, message, error=None, request=None):
        self.message = message
        self.error = error
        self.request = request
        self.discord_webhook_url = settings.DISCORD_WEBHOOK_URL

        discord_alert(
            discord_webhook_url=self.discord_webhook_url,
            message=self.message,
            error=self.error,
            request=self.request,
        )

        super().__init__(message)


class UserNotSubscribedException(Exception):
    """Custom exception for when a user is not subscribed."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "User is not subscribed or out of prompts."

    def __init__(self, message=None):
        if message:
            self.detail = message
        else:
            self.detail = self.default_detail
