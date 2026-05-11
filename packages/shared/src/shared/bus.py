import json
from typing import Any, Callable, Dict, Optional, Coroutine
import redis.asyncio as redis
from .messages import Message

from .config import settings

class MessageBus:
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None, db: Optional[int] = None):
        host = host or settings.redis_host
        port = port or settings.redis_port
        db = db or settings.redis_db
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    async def publish(self, topic: str, message: Message):
        """Publishes a message to a topic (Redis Stream)."""
        data = message.model_dump_json()
        await self.client.xadd(topic, {"data": data})

    async def subscribe(self, topic: str, consumer_group: str, consumer_name: str, callback: Callable[[Any], Coroutine[Any, Any, None]], stop_event: Optional[asyncio.Event] = None):
        """Subscribes to a topic using a consumer group (Async)."""
        import asyncio
        try:
            await self.client.xgroup_create(topic, consumer_group, id="0", mkstream=True)
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

        while stop_event is None or not stop_event.is_set():
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
    async def receive(self, topic: str, timeout: int = 60000) -> Optional[Dict[str, Any]]:
        """Waits for a single message on a topic using blocking read."""
        streams = await self.client.xread({topic: "0"}, count=1, block=timeout)
        if streams:
            for _, messages in streams:
                for _, message_data in messages:
                    return message_data
        return None

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
