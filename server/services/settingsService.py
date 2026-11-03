import os

from config import Config
from services import mailService

# Values left as in secrets.yml.template count as not defined
_PLACEHOLDER_PREFIXES = ("YOUR_", "CHANGE_ME")


def _defined(value):
    if value is None:
        return False
    value = str(value).strip()
    return bool(value) and not value.startswith(_PLACEHOLDER_PREFIXES)


def _aws_credential_chain():
    try:
        import boto3
        return boto3.Session().get_credentials() is not None
    except Exception:
        return False


def _s3(secrets):
    if _defined(secrets.get("s3_access_key_id")) and _defined(secrets.get("s3_secret_access_key")):
        return True, "secrets"
    if _aws_credential_chain():
        return True, "aws"
    return False, None


def _pgpass(secrets):
    path = secrets.get("pgpass_file")
    return _defined(path) and os.path.isfile(path), None


def status():
    """What the server read from config.yml and secrets.yml: whether each integration is set up.

    Only booleans and where a setting came from: never a value, a key or a path.
    """
    config = Config.get_instance()
    secrets = config.get_secrets or {}
    settings = config.get_config or {}
    s3_configured, s3_source = _s3(secrets)
    integrations = [
        ("openai", _defined(secrets.get("openai_api_key")), None),
        ("elevenlabs", _defined(secrets.get("elevenlabs_api_key")), None),
        ("mapbox", _defined(secrets.get("mapbox_access_token")), None),
        ("s3", s3_configured, s3_source),
        ("postgres", *_pgpass(secrets)),
        ("google", _defined(secrets.get("google_client_id")), None),
        ("smtp", mailService.is_configured(), None),
        ("apiSearch", _defined(secrets.get("api_domain")), None),
    ]
    return {
        "files": {"config": bool(settings), "secrets": bool(secrets)},
        "authEnabled": bool(settings.get("authEnabled", False)),
        "integrations": [{"id": i, "configured": bool(c), "source": s} for i, c, s in integrations],
    }
