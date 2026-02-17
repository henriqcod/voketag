import json
from google.cloud import pubsub_v1

from config.settings import get_settings


def publish_scan_event(
    tag_id: str, scan_count: int, first_scan_at: str | None = None
) -> str | None:
    settings = get_settings()
    if not settings.gcp_project_id or not settings.pubsub_topic_scan:
        return None
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(
        settings.gcp_project_id, settings.pubsub_topic_scan
    )
    data = json.dumps(
        {
            "tag_id": tag_id,
            "scan_count": scan_count,
            "first_scan_at": first_scan_at,
        }
    ).encode()
    future = publisher.publish(topic_path, data)
    return future.result()
