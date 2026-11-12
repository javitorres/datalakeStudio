import json
import os
import re
import threading
import time

from services import databaseService
from services.apiServerService import _bind_parameters

# The dashboards of each user, one JSON file per dashboard in their folder. A published one also has a
# copy in PUBLISHED_FOLDER, under the path its author chose (iris/flower_analysis), with the SQL of its
# widgets: other users open it there, and its queries run on the author's database.
FOLDER = "dashboards"
# Not a valid user name (they can't start with a dot), so it can't clash with a user's folder
PUBLISHED_FOLDER = ".published"
MAX_DASHBOARDS = 200
MAX_SQL_LENGTH = 20000
# Rows a widget of a published dashboard can get
MAX_ROWS = 1000
_ID = re.compile(r"[A-Za-z0-9_-]{8,64}")
# Up to five segments of lower case letters, digits, "_" and "-": no dots, so no way out of the folder
_SEGMENT = r"[a-z0-9][a-z0-9_-]{0,49}"
_PATH = re.compile(rf"{_SEGMENT}(/{_SEGMENT}){{0,4}}")
_KEY = re.compile(r"[a-z]\d{1,3}")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
FILTER_TYPES = ("select", "range", "dateRange")
_lock = threading.Lock()


class PathTaken(Exception):
    pass


def _folder():
    folder = os.path.join(databaseService.get_user_folder(), FOLDER)
    os.makedirs(folder, exist_ok=True)
    return folder


def _file(dashboard_id):
    # The id becomes a file name
    if not _ID.fullmatch(dashboard_id or ""):
        raise ValueError(f"Invalid dashboard id: {dashboard_id!r}")
    return os.path.join(_folder(), dashboard_id + ".json")


def _published_folder():
    return os.path.join(databaseService._config["databasesFolder"], PUBLISHED_FOLDER)


def clean_path(path):
    path = (path or "").strip().strip("/").lower()
    if not _PATH.fullmatch(path):
        raise ValueError("Invalid path. Use up to five segments of letters, numbers, '_' and '-' "
                         "separated by '/', such as iris/flower_analysis")
    return path


def _published_file(path):
    return os.path.join(_published_folder(), *clean_path(path).split("/")) + ".json"


def _read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False)
    os.replace(tmp, path)


def _summary(dashboard):
    return {k: dashboard.get(k) for k in ("id", "title", "database", "created", "updated", "published")}


####################################################
def list_dashboards():
    """The user's dashboards without their specification, most recent first."""
    folder = _folder()
    found = []
    for name in os.listdir(folder):
        if name.endswith(".json"):
            dashboard = _read(os.path.join(folder, name))
            if dashboard:
                found.append(_summary(dashboard))
    return sorted(found, key=lambda d: d["updated"] or 0, reverse=True)


def get_dashboard(dashboard_id):
    return _read(_file(dashboard_id))


def save_dashboard(dashboard_id, title, spec, history=None, database=None):
    file = _file(dashboard_id)
    now = time.time()
    with _lock:
        previous = _read(file) or {}
        if not previous and len(os.listdir(_folder())) >= MAX_DASHBOARDS:
            raise ValueError(f"You can keep up to {MAX_DASHBOARDS} dashboards: delete one first")
        dashboard = {"id": dashboard_id, "title": title, "database": previous.get("database") or database,
                     "created": previous.get("created", now), "updated": now,
                     "published": previous.get("published"), "spec": spec, "history": history or []}
        _write(file, dashboard)
    return dashboard


def delete_dashboard(dashboard_id):
    file = _file(dashboard_id)
    with _lock:
        dashboard = _read(file)
        if dashboard is None:
            return False
        _remove_published(dashboard)
        os.remove(file)
    return True


####################################################
def _remove_published(dashboard):
    published = dashboard.get("published")
    if not published:
        return
    file = _published_file(published["path"])
    record = _read(file)
    # Only its own copy: the path may have been taken by another dashboard since
    if record and (record["owner"], record["id"]) == (databaseService.get_current_user(), dashboard["id"]):
        os.remove(file)


def _filters(spec):
    filters = spec.get("filters") or []
    for f in filters:
        if not isinstance(f, dict) or not _KEY.fullmatch(str(f.get("id"))) or f.get("type") not in FILTER_TYPES:
            raise ValueError("Invalid filter in the dashboard")
    return filters


def _number(value):
    try:
        return float(value) if value is not None and value != "" else None
    except (TypeError, ValueError):
        return None


def _date(value):
    return value[:10] if isinstance(value, str) and _DATE.fullmatch(value[:10]) else None


def filter_values(spec, state):
    """The value of every {placeholder} of the dashboard's queries, from the filters a viewer set
    ({filter id: value}). A filter that isn't set, or has an invalid value, is None: it doesn't filter."""
    values = {}
    for f in _filters(spec):
        key, value = f["id"], state.get(f["id"])
        if f["type"] == "select":
            chosen = [str(v)[:500] for v in value[:200]] if isinstance(value, list) else []
            values[key] = chosen or None
            continue
        low, high = (list(value) + [None, None])[:2] if isinstance(value, (list, tuple)) else (None, None)
        if f["type"] == "range":
            values[key + "_min"], values[key + "_max"] = _number(low), _number(high)
        else:
            values[key + "_from"], values[key + "_to"] = _date(low), _date(high)
    return values


def publish_dashboard(dashboard_id, path, queries):
    """Publish the saved dashboard under `path`, with the SQL of its widgets and filters."""
    path = clean_path(path)
    owner = databaseService.get_current_user()
    file = _file(dashboard_id)
    with _lock:
        dashboard = _read(file)
        if dashboard is None:
            return None
        spec = dashboard["spec"]
        keys = {str(item.get("id")) for kind in ("widgets", "filters") for item in spec.get(kind) or []}
        database = databaseService.get_current_database_name()
        values = filter_values(spec, {})
        for key, sql in queries.items():
            if key not in keys or not _KEY.fullmatch(key):
                raise ValueError(f"Unknown widget or filter: {key}")
            if len(sql) > MAX_SQL_LENGTH:
                raise ValueError(f"The query of {key} is too long")
            # Each query must be a single SELECT that runs, with no filter set
            bound, params = _bind_parameters(sql, values)
            databaseService.runQueryAs(owner, database, bound, params, rows=1)

        published_file = _published_file(path)
        taken = _read(published_file)
        if taken and (taken["owner"], taken["id"]) != (owner, dashboard_id):
            raise PathTaken(f"The path {path} is already used by another dashboard")
        if dashboard.get("published") and dashboard["published"]["path"] != path:
            _remove_published(dashboard)

        now = time.time()
        _write(published_file, {"path": path, "owner": owner, "id": dashboard_id, "database": database,
                                "title": dashboard["title"], "published": now, "spec": spec, "queries": queries})
        dashboard["published"] = {"path": path, "updated": now}
        dashboard["database"] = database
        _write(file, dashboard)
    return _summary(dashboard)


def unpublish_dashboard(dashboard_id):
    file = _file(dashboard_id)
    with _lock:
        dashboard = _read(file)
        if dashboard is None:
            return None
        _remove_published(dashboard)
        dashboard["published"] = None
        _write(file, dashboard)
    return _summary(dashboard)


####################################################
def _public(record):
    """What a viewer gets of a published dashboard: never its SQL."""
    spec = dict(record["spec"])
    spec["datasets"] = [{k: v for k, v in dataset.items() if k != "sql"} for dataset in spec.get("datasets") or []]
    return {"path": record["path"], "title": record["title"], "owner": record["owner"],
            "published": record["published"], "spec": spec}


def list_published():
    """Every published dashboard, by path."""
    found = []
    for folder, _, names in os.walk(_published_folder()):
        for name in names:
            if name.endswith(".json"):
                record = _read(os.path.join(folder, name))
                if record:
                    found.append({k: record.get(k) for k in ("path", "title", "owner", "published")})
    return sorted(found, key=lambda d: d["path"])


def get_published(path):
    record = _read(_published_file(path))
    return _public(record) if record else None


def run_published(path, key, state):
    """The rows of a widget or filter of a published dashboard, for the filters the viewer set. Viewers
    never send SQL: the stored query runs on the author's database with their values as parameters."""
    record = _read(_published_file(path))
    if record is None or key not in record["queries"]:
        return None
    sql, params = _bind_parameters(record["queries"][key], filter_values(record["spec"], state or {}))
    return databaseService.runQueryAs(record["owner"], record["database"], sql, params, rows=MAX_ROWS)
