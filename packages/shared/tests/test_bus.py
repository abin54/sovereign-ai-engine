import pytest
import json
from unittest.mock import AsyncMock, patch
from shared.bus import MessageBus
from shared.messages import Message, TaskRequest

@pytest.mark.asyncio
async def test_publish():
    with patch("redis.asyncio.Redis") as mock_redis:
        mock_client = AsyncMock()
        mock_redis.return_value = mock_client
        
        bus = MessageBus()
        message = TaskRequest(
            task_id="task1",
            skill_name="s1",
            action="a1",
            input_data={}
        )
        
        await bus.publish("test_topic", message)
        
        mock_client.xadd.assert_called_once()
        args, kwargs = mock_client.xadd.call_args
        assert args[0] == "test_topic"
        assert "data" in args[1]
        assert json.loads(args[1]["data"])["task_id"] == "task1"

@pytest.mark.asyncio
async def test_register_and_get_services():
    with patch("redis.asyncio.Redis") as mock_redis:
        mock_client = AsyncMock()
        mock_redis.return_value = mock_client
        
        bus = MessageBus()
        
        # Test Registration
        metadata = {"service_type": "skill", "capabilities": ["shell"]}
        await bus.register_service("skill-1", metadata)
        mock_client.set.assert_called_once_with(
            "service_registry:skill-1", 
            json.dumps(metadata), 
            ex=60
        )
        
        # Test Discovery
        mock_client.keys.return_value = ["service_registry:skill-1"]
        mock_client.get.return_value = json.dumps(metadata)
        
        services = await bus.get_services(service_type="skill")
        assert "skill-1" in services
        assert services["skill-1"]["service_type"] == "skill"
