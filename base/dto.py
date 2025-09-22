from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class ProductData(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class PaymentSessionData(BaseModel):
    product_data: ProductData = Field(default_factory=lambda: ProductData(name="Product"))
    unit_amount: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
