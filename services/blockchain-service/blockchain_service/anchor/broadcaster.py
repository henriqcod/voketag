from typing import Optional
from google.cloud import pubsub_v1


class Broadcaster:
    def __init__(self, project_id: str, topic_id: str):
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(project_id, topic_id)

    def broadcast(self, merkle_root: str, tx_hash: str) -> Optional[str]:
        future = self.publisher.publish(
            self.topic_path,
            data=merkle_root.encode(),
            tx_hash=tx_hash,
        )
        return future.result()
