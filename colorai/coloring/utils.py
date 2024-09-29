import os


def upload_file_lowercase_name(instance, filename):
    """Transform path filename to lower"""
    path = getattr(instance, "upload_path", "")
    return f"{path}{filename.lower()}"
