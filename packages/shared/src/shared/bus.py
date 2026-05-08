import json
from typing import Any, Callable, Dict, Optional
import redis
from .messages import Message

class MessageBus:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def publish(self, topic: str, message: Message):
        """Publishes a message to a topic (Redis Stream)."""
        data = message.model_dump_json()
        self.client.xadd(topic, {"data": data})

    def subscribe(self, topic: str, consumer_group: str, consumer_name: str, callback: Callable[[Message], None]):
        """Subscribes to a topic using a consumer group."""
        try:
            self.client.xgroup_create(topic, consumer_group, id="0", mkstream=True)
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

        while True:
            # Read new messages
            streams = self.client.xreadgroup(consumer_group, consumer_name, {topic: ">"}, count=1, block=1000)
            for stream_topic, messages in streams:
                for message_id, message_data in messages:
                    raw_data = message_data["data"]
                    # Here we would need to know the message type to deserialize
                    # For now, we'll just pass the raw JSON or a generic Message
                    # A better way is to pass the message class to the subscriber
                    print(f"Received message on {stream_topic}: {raw_data}")
                    # Acknowledge
                    self.client.xack(topic, consumer_group, message_id)

    def register_service(self, service_id: str, metadata: Dict[str, Any], ttl: int = 60):
        """Registers a service in the registry with a TTL."""
        key = f"service_registry:{service_id}"
        self.client.set(key, json.dumps(metadata), ex=ttl)

    def get_services(self, service_type: Optional[str] = None) -> Dict[str, Any]:
        """Discovers available services."""
        services = {}
        keys = self.client.keys("service_registry:*")
        for key in keys:
            data = json.loads(self.client.get(key))
            if not service_type or data.get("service_type") == service_type:
                services[key.split(":")[-1]] = data
        return services
