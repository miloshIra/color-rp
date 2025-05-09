import json
import os
import traceback
from datetime import datetime

import requests

from colorai import settings

discord_webhook_url = settings.DISCORD_WEBHOOK_URL


def upload_file_lowercase_name(instance, filename):
    """Transform path filename to lower"""
    path = getattr(instance, "upload_path", "")
    return f"{path}{filename.lower()}"


def discord_alert(
    *, discord_webhook_url: str, message: str, error=None, request=None
) -> str:
    def get_error_message(error):
        if error:

            trace_back = traceback.extract_tb(error.__traceback__)

            if trace_back:
                last_trace_back = trace_back[-1]
                return last_trace_back.name
            return "Unknown error"
        return None

    function_name = get_error_message(error) if error else None
    stack_trace = (
        "".join(traceback.format_exception(type(error), error, error.__traceback__))
        if error
        else None
    )

    more_info = {
        "user": request.user.username if request else None,
        "request_method": request.method if request else None,
        "request_path": request.path if request else None,
    }

    timestamp = str(datetime.now()).split(".")[0]

    payload = {
        "content": (
            f"👀 **SOURCE**: ColorAI\n"
            f"🚨 **Error**: {message}\n"
            f"📝 **Function**: {function_name}\n"
            f"⌚ **Timestamp**: {timestamp}\n"
            f"📜 **Stack**: {stack_trace}\n"
            f"📊 **More Info**: {json.dumps(more_info)}\n"
            f"--------------------------------"
        )
    }

    requests.post(
        discord_webhook_url,
        headers={"Content-Type": "application/json"},
        json=payload,
    )


def discord_prompt_stats(
    *,
    discord_webhook_url: str,
    prompts: int,
    size: str,
    bill: str,
    user: str,
) -> str:

    timestamp = str(datetime.now()).split(".")[0]
    more_info = {"user": user}

    payload = {
        "content": (
            f"👀 **SOURCE**: ColoringAI:\n"
            f"🚨 **Total prompts**: {prompts}\n"
            f"📝 **Est storage size**: {size}\n"
            f"⌚ **Timestamp**: {timestamp}\n"
            f"📊 **Cost so far**: {bill}\n"
            f"📊 **More Info**: {json.dumps(more_info)}\n"
            f"--------------------------------"
        )
    }

    requests.post(
        discord_webhook_url,
        headers={"Content-Type": "application/json"},
        json=payload,
    )


def discord_user_stats(
    *,
    discord_webhook_url: str,
    number: int,
) -> str:

    timestamp = str(datetime.now()).split(".")[0]
    more_info = {}

    payload = {
        "content": (
            f"👀 **SOURCE**: ColoringAI:\n"
            f"🚨 **Total users**: {number}\n"
            # f"📝 **Est storage size**: {size}\n"
            # f"⌚ **Timestamp**: {timestamp}\n"
            # f"📊 **Cost so far**: {bill}\n"
            # f"📊 **More Info**: {json.dumps(more_info)}\n"
            f"--------------------------------"
        )
    }

    requests.post(
        discord_webhook_url,
        headers={"Content-Type": "application/json"},
        json=payload,
    )


def discord_subscription_stats(
    *,
    discord_webhook_url: str,
    user: str,
    action: str,
) -> str:

    timestamp = str(datetime.now()).split(".")[0]

    payload = {
        "content": (
            f"💰 **SOURCE**: ColoringAI:\n"
            f"📝 **Users with email**: {user}\n"
            f"🚨 **Action**: {action}\n"
            f"⌚ **Timestamp**: {timestamp}\n"
            # f"📊 **More Info**: {json.dumps(more_info)}\n"
            # if more_info
            # else ""
            # f" ** Total subscriptions is now at {total_subs}\n"
            f"--------------------------------------"
        )
    }

    requests.post(
        discord_webhook_url,
        headers={"Content-Type": "application/json"},
        json=payload,
    )
