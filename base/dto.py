from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class ProductData(BaseModel):
    name: str = Field(min_length=1, max_length=255, default="Product #1")
    description: str = Field(default="Good choice")


class PaymentSessionData(BaseModel):
    product_data: ProductData = Field(default_factory=lambda: ProductData())
    unit_amount: Decimal = Field(..., gt=Decimal("0.0"))
    quantity: int = Field(..., gt=0)


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    CANCELED = "CANCELED"
    EXPIRED = "EXPIRED"


class PaymentType(str, Enum):
    PAYMENT = "PAYMENT"
    FINE = "FINE"


class PaymentData(BaseModel):
    status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    type: PaymentType = Field(default=PaymentType.PAYMENT)
    fine_multiplier: Decimal = Field(gt=Decimal("0.0"), default=Decimal("1.0"))
    product_data: ProductData = Field(default_factory=lambda: ProductData())
    price: Decimal = Field(gt=Decimal("0.0"), default=Decimal("1.0"))
    rent_days: int = Field(gt=1, default=1)
