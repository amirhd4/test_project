import json
from typing import Any

import structlog
from aiokafka import AIOKafkaProducer

from order_service.app.config import settings

logger = structlog.get_logger(__name__)


class KafkaService:
    def __init__(self) -> None:
        self.producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                retry_backoff_ms=500,
            )
            await self.producer.start()
            logger.info(
                "Kafka Producer started successfully",
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            )
        except Exception as e:
            logger.warning(
                "Could not connect to Kafka, running producer in mock mode",
                error=str(e),
            )
            self.producer = None

    async def stop(self) -> None:
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka Producer stopped")

    async def send_order_event(self, event_data: dict[str, Any]) -> bool:
        if not self.producer:
            logger.info(
                "Kafka Producer offline/mocked. Event logged instead of sent.",
                event_data=event_data,
            )
            return False
        try:
            await self.producer.send_and_wait(
                settings.KAFKA_ORDER_EVENTS_TOPIC,
                value=event_data,
                key=event_data.get("order_id", "").encode("utf-8"),
            )
            logger.info(
                "Kafka event sent successfully",
                topic=settings.KAFKA_ORDER_EVENTS_TOPIC,
                order_id=event_data.get("order_id"),
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to send Kafka event",
                error=str(e),
                order_id=event_data.get("order_id"),
            )
            return False


kafka_service = KafkaService()
