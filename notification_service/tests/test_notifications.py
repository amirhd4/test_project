import pytest
from httpx import AsyncClient

from notification_service.app.kafka_consumer import kafka_consumer_service


@pytest.mark.asyncio
async def test_notification_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data


@pytest.mark.asyncio
async def test_event_processing_and_notifications_list(client: AsyncClient) -> None:
    # Simulate processing an OrderCreated event
    event = {
        "event_type": "OrderCreated",
        "order_id": "ord-test-999",
        "customer_id": "cust-test-888",
        "total_price": 199.99,
        "items": [],
        "created_at": "2025-01-01T00:00:00Z",
    }

    await kafka_consumer_service.process_event(event)

    response = await client.get("/api/v1/notifications")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    notification = data[0]
    assert notification["order_id"] == "ord-test-999"
    assert notification["customer_id"] == "cust-test-888"
    assert "199.99" in notification["message"]
