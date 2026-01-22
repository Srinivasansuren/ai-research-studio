# app/pipeline/pubsub_client.py
import json
import os
from google.cloud import pubsub_v1

from .contracts import FetchRequestV1


class FetchPublisher:
    """
    Phase IV publisher:
    - Publishes fetch requests to Pub/Sub
    - Synchronous publish (fire-and-forget)
    - No retries, no async orchestration here
    """

    def __init__(self):
        project_id = os.environ["GCP_PROJECT"]
        topic_name = os.environ["FETCH_REQUESTS_TOPIC"]

        self._topic_path = f"projects/{project_id}/topics/{topic_name}"
        self._publisher = pubsub_v1.PublisherClient()

    def publish(self, req: FetchRequestV1) -> str:
        payload = json.dumps(req.to_dict()).encode("utf-8")

        future = self._publisher.publish(
            self._topic_path,
            payload,
            version=req.VERSION,
        )

        # Block only until Pub/Sub accepts the message
        message_id = future.result(timeout=10)
        return message_id
