import asyncio
import json

import structlog
from aiokafka import AIOKafkaConsumer

from notification_service.app.config import settings
from notification_service.app.database import AsyncSessionLocal
from notification_service.app.models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
)

logger = structlog.get_logger(__name__)


class KafkaConsumerService:
    def __init__(self) -> None:
        self.consumer: AIOKafkaConsumer | None = None
        self.is_running: bool = False
        self.task: asyncio.Task | None = None

    async def start(self) -> None:
        self.is_running = True
        self.task = asyncio.create_task(self._consume_loop())

    async def _consume_loop(self) -> None:
        try:
            self.consumer = AIOKafkaConsumer(
                settings.KAFKA_ORDER_EVENTS_TOPIC,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=settings.KAFKA_CONSUMER_GROUP,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                auto_offset_reset="earliest",
            )
            await self.consumer.start()
            logger.info(
                "Kafka Consumer started",
                topic=settings.KAFKA_ORDER_EVENTS_TOPIC,
                group=settings.KAFKA_CONSUMER_GROUP,
            )

            async for msg in self.consumer:
                if not self.is_running:
                    break
                logger.info(
                    "Received Kafka message",
                    topic=msg.topic,
                    partition=msg.partition,
                    offset=msg.offset,
                )
                await self.process_event(msg.value)

        except asyncio.CancelledError:
            logger.info("Consumer loop cancelled")
        except Exception as e:
            logger.warning("Kafka consumer unavailable or connection lost", error=str(e))
        finally:
            if self.consumer:
                await self.consumer.stop()
                logger.info("Kafka Consumer stopped")

    async def process_event(self, event_data: dict) -> None:
        try:
            event_type = event_data.get("event_type")
            order_id = event_data.get("order_id")
            customer_id = event_data.get("customer_id")
            total_price = event_data.get("total_price")

            logger.info("Processing order event", event_type=event_type, order_id=order_id)

            if event_type == "OrderCreated":
                msg_str = (
                    f"Hello Customer {customer_id}, your order #{order_id} "
                    f"totaling ${total_price:.2f} has been confirmed!"
                )

                async with AsyncSessionLocal() as session:
                    notification = Notification(
                        order_id=str(order_id),
                        customer_id=str(customer_id),
                        channel=NotificationChannel.EMAIL,
                        recipient=f"{customer_id}@example.com",
                        message=msg_str,
                        status=NotificationStatus.SENT,
                    )
                    session.add(notification)
                    await session.commit()
                    logger.info(
                        "Notification log recorded",
                        notification_id=notification.id,
                        order_id=order_id,
                    )

        except Exception as e:
            logger.error("Failed to process event", error=str(e), event_data=event_data)

    async def stop(self) -> None:
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass


kafka_consumer_service = KafkaConsumerService()
