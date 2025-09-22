from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class ProductData(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class PaymentSessionData(BaseModel):
    product_data: ProductData = Field(default_factory=lambda: ProductData(name="Product"))
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
