from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from order_service.app.models import OrderStatus


class OrderItemSchema(BaseModel):
    product_id: str = Field(..., json_schema_extra={"example": "prod-101"})
    product_name: str = Field(..., json_schema_extra={"example": "Laptop Pro Max"})
    quantity: int = Field(..., gt=0, json_schema_extra={"example": 1})
    unit_price: float = Field(..., gt=0, json_schema_extra={"example": 1200.00})


class OrderCreateSchema(BaseModel):
    customer_id: str = Field(..., json_schema_extra={"example": "cust-555"})
    items: list[OrderItemSchema] = Field(..., min_length=1)


class OrderResponseSchema(BaseModel):
    id: str
    customer_id: str
    items: list[dict[str, Any]]
    total_price: float
    status: OrderStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdateSchema(BaseModel):
    status: OrderStatus


class OrderCreatedKafkaEvent(BaseModel):
    event_id: str
    event_type: str = "OrderCreated"
    order_id: str
    customer_id: str
    total_price: float
    items: list[dict[str, Any]]
    created_at: str
