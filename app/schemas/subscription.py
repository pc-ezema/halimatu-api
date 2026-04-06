from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List
from enum import Enum

class PlanType(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    BI_ANNUAL = "bi_annual"
    ANNUAL = "annual"

class PlanCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    type: PlanType
    duration_months: int = Field(..., ge=1, le=24)
    original_price: float = Field(..., gt=0)
    discounted_price: float = Field(..., gt=0)
    discount_percentage: Optional[int] = Field(None, ge=0, le=100)
    description: Optional[str] = None
    features: Optional[List[str]] = []
    status: Optional[str] = "active"
    sort_order: int = 0

class PlanUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    original_price: Optional[float] = Field(None, gt=0)
    discounted_price: Optional[float] = Field(None, gt=0)
    discount_percentage: Optional[int] = Field(None, ge=0, le=100)
    description: Optional[str] = None
    features: Optional[List[str]] = None
    status: Optional[str] = None
    sort_order: Optional[int] = None

class PlanResponse(BaseModel):
    id: int
    name: str
    type: PlanType
    duration_months: int
    original_price: float
    discounted_price: float
    discount_percentage: int
    description: Optional[str]
    features: List[str]
    sort_order: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class SubscribeRequest(BaseModel):
    plan_id: int
    payment_method: str  # card, bank_transfer, ussd, wallet
    auto_renew: bool = False

class SubscriptionResponse(BaseModel):
    id: int
    subscription_id: str
    user_id: int
    plan: PlanResponse
    amount_paid: float
    start_date: datetime
    end_date: datetime
    status: str
    auto_renew: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class PaymentResponse(BaseModel):
    id: int
    transaction_id: str
    amount: float
    payment_method: str
    status: str
    paid_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    message: str

# Plan with User's Subscription Status
class PlanWithUserStatusResponse(PlanResponse):
    """Plan response with user's subscription status"""
    is_current_plan: bool = False
    subscription_status: Optional[str] = None
    subscription_end_date: Optional[datetime] = None
    days_remaining: int = 0
    
    class Config:
        from_attributes = True
