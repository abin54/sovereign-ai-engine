import json
from typing import Any, Callable, Dict, Optional, Coroutine
import redis.asyncio as redis
from .messages import Message

class MessageBus:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    async def publish(self, topic: str, message: Message):
        """Publishes a message to a topic (Redis Stream)."""
        data = message.model_dump_json()
        await self.client.xadd(topic, {"data": data})

    async def subscribe(self, topic: str, consumer_group: str, consumer_name: str, callback: Callable[[Any], Coroutine[Any, Any, None]]):
        """Subscribes to a topic using a consumer group (Async)."""
        try:
            await self.client.xgroup_create(topic, consumer_group, id="0", mkstream=True)
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

        while True:
            # Read new messages
            streams = await self.client.xreadgroup(consumer_group, consumer_name, {topic: ">"}, count=1, block=1000)
            if streams:
                for stream_topic, messages in streams:
                    for message_id, message_data in messages:
                        # Wrap the raw data in a mock object that matches the previous structure
                        # Or just pass the raw message_data
                        class MockMessage:
                            def __init__(self, data): self.data = data
                        
                        await callback(MockMessage(message_data))
                        # Acknowledge
                        await self.client.xack(topic, consumer_group, message_id)

    async def register_service(self, service_id: str, metadata: Dict[str, Any], ttl: int = 60):
        """Registers a service in the registry with a TTL."""
        key = f"service_registry:{service_id}"
        await self.client.set(key, json.dumps(metadata), ex=ttl)

    async def get_services(self, service_type: Optional[str] = None) -> Dict[str, Any]:
        """Discovers available services."""
        services = {}
        keys = await self.client.keys("service_registry:*")
        for key in keys:
            val = await self.client.get(key)
            data = json.loads(val)
            if not service_type or data.get("service_type") == service_type:
                services[key.split(":")[-1]] = data
        return services
