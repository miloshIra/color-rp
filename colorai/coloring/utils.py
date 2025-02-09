import json
import os
import traceback
from datetime import datetime

import requests

discord_webhook_url = "https://discord.com/api/webhooks/1338091856193523712/irclCWU3Xuk8id7D9nvqXBhWAoaeu0xESmnBW5KWrkY9mH8v2EFa4t1yd_ddw13OE9py"


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

    print("Alert sent to Discord")
    return "Alert sent to Discord"
