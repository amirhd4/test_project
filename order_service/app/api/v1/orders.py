import uuid
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from order_service.app.database import get_db
from order_service.app.kafka_producer import kafka_service
from order_service.app.models import Order, OrderStatus
from order_service.app.schemas import (
    OrderCreatedKafkaEvent,
    OrderCreateSchema,
    OrderResponseSchema,
    OrderStatusUpdateSchema,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_in: OrderCreateSchema,
    db: AsyncSession = Depends(get_db),
) -> Order:
    """Create a new order and publish an OrderCreated event to Kafka."""
    # Calculate total price
    total_price = sum(item.quantity * item.unit_price for item in order_in.items)
    items_dict = [item.model_dump() for item in order_in.items]

    new_order = Order(
        id=str(uuid.uuid4()),
        customer_id=order_in.customer_id,
        items=items_dict,
        total_price=total_price,
        status=OrderStatus.PENDING,
    )

    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)

    logger.info("Order created in DB", order_id=new_order.id, customer_id=new_order.customer_id)

    # Publish Kafka event
    event = OrderCreatedKafkaEvent(
        event_id=str(uuid.uuid4()),
        order_id=new_order.id,
        customer_id=new_order.customer_id,
        total_price=new_order.total_price,
        items=new_order.items,
        created_at=datetime.now(UTC).isoformat(),
    )

    await kafka_service.send_order_event(event.model_dump())

    return new_order


@router.get("/", response_model=list[OrderResponseSchema])
async def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[Order]:
    """Retrieve orders with pagination."""
    query = select(Order).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{order_id}", response_model=OrderResponseSchema)
async def get_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
) -> Order:
    """Retrieve details for a specific order."""
    query = select(Order).where(Order.id == order_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/{order_id}/status", response_model=OrderResponseSchema)
async def update_order_status(
    order_id: str,
    status_in: OrderStatusUpdateSchema,
    db: AsyncSession = Depends(get_db),
) -> Order:
    """Update status of an order."""
    query = select(Order).where(Order.id == order_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = status_in.status
    await db.commit()
    await db.refresh(order)
    logger.info("Order status updated", order_id=order.id, new_status=order.status)
    return order
