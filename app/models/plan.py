from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base
import enum

class PlanType(str, enum.Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    BI_ANNUAL = "bi_annual"
    ANNUAL = "annual"

class PlanStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(Enum(PlanType), nullable=False, unique=True)
    duration_months = Column(Integer, nullable=False)  # 1, 3, 6, 12
    original_price = Column(Float, nullable=False)
    discounted_price = Column(Float, nullable=False)
    discount_percentage = Column(Integer, default=0)
    description = Column(Text, nullable=True)
    features = Column(JSON, default=list)  # List of features
    status = Column(Enum(PlanStatus), default=PlanStatus.ACTIVE)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="plan", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Plan {self.name} - ₦{self.discounted_price}>"