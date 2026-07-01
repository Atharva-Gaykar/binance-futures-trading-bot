"""
Input validation for trading bot orders.
Uses Pydantic models to validate CLI input before hitting the Binance API.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LIMIT = "STOP"  # bonus order type


class OrderRequest(BaseModel):
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None       # required for LIMIT and STOP_LIMIT
    stop_price: Optional[float] = None  # required for STOP_LIMIT only

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        v = v.strip().upper()
        if not v.endswith("USDT"):
            raise ValueError(
                f"Symbol '{v}' invalid — this bot only supports USDT-M pairs (e.g., BTCUSDT)"
            )
        return v

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("Price must be greater than 0")
        return v

    @field_validator("stop_price")
    @classmethod
    def validate_stop_price(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("Stop price must be greater than 0")
        return v

    @model_validator(mode="after")
    def validate_price_requirements(self) -> "OrderRequest":
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError("Price is required for LIMIT orders")

        if self.order_type == OrderType.STOP_LIMIT:
            if self.price is None:
                raise ValueError("Price is required for STOP_LIMIT orders")
            if self.stop_price is None:
                raise ValueError("Stop price is required for STOP_LIMIT orders")

        return self