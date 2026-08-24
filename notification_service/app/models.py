import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from notification_service.app.database import Base


class NotificationStatus(enum.StrEnum):
    SENT = "SENT"
    FAILED = "FAILED"
    PENDING = "PENDING"


class NotificationChannel(enum.StrEnum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    order_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel), default=NotificationChannel.EMAIL, nullable=False
    )
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus), default=NotificationStatus.SENT, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
