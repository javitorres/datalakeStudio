import json
import os
import re
import threading
import time

from services import databaseService

# The assistant conversations of each user, one JSON file per conversation in their folder
FOLDER = "conversations"
MAX_CONVERSATIONS = 100
_ID = re.compile(r"[A-Za-z0-9_-]{8,64}")
_lock = threading.Lock()


def _folder():
    folder = os.path.join(databaseService.get_user_folder(), FOLDER)
    os.makedirs(folder, exist_ok=True)
    return folder


def _path(conversation_id):
    # The id becomes a file name
    if not _ID.fullmatch(conversation_id or ""):
        raise ValueError(f"Invalid conversation id: {conversation_id!r}")
    return os.path.join(_folder(), conversation_id + ".json")


def _read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _write(path, conversation):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(conversation, f, ensure_ascii=False)
    os.replace(tmp, path)


def list_conversations():
    """The conversations without their messages, most recent first."""
    folder = _folder()
    found = []
    for name in os.listdir(folder):
        if name.endswith(".json"):
            conversation = _read(os.path.join(folder, name))
            if conversation:
                found.append({k: conversation.get(k) for k in ("id", "title", "database", "created", "updated")})
    return sorted(found, key=lambda c: c["updated"] or 0, reverse=True)


def get_conversation(conversation_id):
    return _read(_path(conversation_id))


def save_conversation(conversation_id, title, messages, database=None):
    path = _path(conversation_id)
    now = time.time()
    with _lock:
        previous = _read(path) or {}
        conversation = {"id": conversation_id, "title": title, "database": database,
                        "created": previous.get("created", now), "updated": now, "messages": messages}
        _write(path, conversation)
        _prune()
    return conversation


def rename_conversation(conversation_id, title):
    path = _path(conversation_id)
    with _lock:
        conversation = _read(path)
        if conversation is None:
            return None
        conversation["title"] = title
        _write(path, conversation)
    return conversation


def delete_conversation(conversation_id):
    path = _path(conversation_id)
    with _lock:
        if not os.path.exists(path):
            return False
        os.remove(path)
    return True


def _prune():
    # Only the most recent ones are kept
    for old in list_conversations()[MAX_CONVERSATIONS:]:
        os.remove(_path(old["id"]))
