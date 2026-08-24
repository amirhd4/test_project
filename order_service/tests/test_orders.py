import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data


@pytest.mark.asyncio
async def test_create_order(client: AsyncClient) -> None:
    order_payload = {
        "customer_id": "cust-test-100",
        "items": [
            {
                "product_id": "prod-1",
                "product_name": "Mechanical Keyboard",
                "quantity": 2,
                "unit_price": 75.50,
            },
            {
                "product_id": "prod-2",
                "product_name": "Gaming Mouse",
                "quantity": 1,
                "unit_price": 49.00,
            },
        ],
    }

    response = await client.post("/api/v1/orders/", json=order_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["customer_id"] == "cust-test-100"
    assert data["total_price"] == (2 * 75.50) + (1 * 49.00)
    assert data["status"] == "PENDING"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_orders(client: AsyncClient) -> None:
    # Create an order first
    order_payload = {
        "customer_id": "cust-test-200",
        "items": [
            {
                "product_id": "prod-3",
                "product_name": "Monitor",
                "quantity": 1,
                "unit_price": 300.00,
            }
        ],
    }
    await client.post("/api/v1/orders/", json=order_payload)

    response = await client.get("/api/v1/orders/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_order_by_id(client: AsyncClient) -> None:
    order_payload = {
        "customer_id": "cust-test-300",
        "items": [
            {
                "product_id": "prod-4",
                "product_name": "Headphones",
                "quantity": 1,
                "unit_price": 120.00,
            }
        ],
    }
    res_create = await client.post("/api/v1/orders/", json=order_payload)
    created_order = res_create.json()
    order_id = created_order["id"]

    response = await client.get(f"/api/v1/orders/{order_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == order_id
    assert data["customer_id"] == "cust-test-300"


@pytest.mark.asyncio
async def test_update_order_status(client: AsyncClient) -> None:
    order_payload = {
        "customer_id": "cust-test-400",
        "items": [
            {
                "product_id": "prod-5",
                "product_name": "Desk Mat",
                "quantity": 1,
                "unit_price": 25.00,
            }
        ],
    }
    res_create = await client.post("/api/v1/orders/", json=order_payload)
    order_id = res_create.json()["id"]

    patch_payload = {"status": "CONFIRMED"}
    response = await client.patch(f"/api/v1/orders/{order_id}/status", json=patch_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CONFIRMED"
