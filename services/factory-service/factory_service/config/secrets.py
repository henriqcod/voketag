from typing import Optional
from factory_service.config.settings import get_settings


def load_secret(secret_name: str, default: Optional[str] = None) -> str:
    """Carrega secret do Secret Manager em prod (sem fallback env). Env apenas em dev."""
    settings = get_settings()
    if settings.env == "production" and settings.gcp_project_id:
        from google.cloud import secretmanager

        client = secretmanager.SecretManagerServiceClient()
        name = (
            f"projects/{settings.gcp_project_id}/secrets/{secret_name}/versions/latest"
        )
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    import os

    env_key = secret_name.upper().replace("-", "_")
    val = os.getenv(env_key)
    if val:
        return val
    if default is not None:
        return default
    raise ValueError(f"Secret {secret_name} not found (env={env_key})")
