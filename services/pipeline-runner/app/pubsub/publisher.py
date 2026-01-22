from __future__ import annotations

import json
from google.cloud import pubsub_v1


class PubSubPublisher:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self._publisher = None

    @property
    def publisher(self):
        if self._publisher is None:
            self._publisher = pubsub_v1.PublisherClient()
        return self._publisher


    def _client(self) -> pubsub_v1.PublisherClient:
        # Client is created lazily, only when needed
        return pubsub_v1.PublisherClient()

    def publish_json(
        self,
        topic_name: str,
        payload: dict,
        attributes: dict | None = None,
    ) -> str:
        publisher = self._client()
        topic_path = publisher.topic_path(self.project_id, topic_name)

        data = json.dumps(
            payload,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

        future = publisher.publish(
            topic_path,
            data=data,
            **(attributes or {}),
        )
        return future.result()
