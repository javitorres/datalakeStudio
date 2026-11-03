import json
import os
import re
import threading

from services import databaseService

# What each user chose in the app settings, in their folder: they follow them to any browser
FILE = "preferences.json"
LOCALES = ("en", "es")
VOICE_PROVIDERS = ("elevenlabs", "openai")
_MODEL = re.compile(r"[A-Za-z0-9._:-]{1,100}")
_lock = threading.Lock()


def _validators():
    return {
        "locale": lambda v: v in LOCALES,
        "voiceProvider": lambda v: v in VOICE_PROVIDERS,
        # None: the model in config.yml
        "aiModel": lambda v: v is None or (isinstance(v, str) and _MODEL.fullmatch(v)),
    }


def _path():
    return os.path.join(databaseService.get_user_folder(), FILE)


def get():
    """The current user's preferences; {} without a user (or before they choose anything)."""
    if databaseService.get_current_user() is None:
        return {}
    try:
        with open(_path(), encoding="utf-8") as f:
            stored = json.load(f)
    except (OSError, ValueError):
        return {}
    validators = _validators()
    return {k: v for k, v in stored.items() if k in validators and validators[k](v)}


def update(changes):
    """Saves the given preferences (unknown names or invalid values raise ValueError) and returns them all."""
    validators = _validators()
    for name, value in changes.items():
        if name not in validators:
            raise ValueError(f"Unknown preference: {name}")
        if not validators[name](value):
            raise ValueError(f"Invalid value for {name}: {value!r}")
    with _lock:
        preferences = {**get(), **changes}
        path = _path()
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(preferences, f, ensure_ascii=False)
        os.replace(tmp, path)
    return preferences
