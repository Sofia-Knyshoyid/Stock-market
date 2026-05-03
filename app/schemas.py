from typing import Literal

from pydantic import BaseModel, Field


class StockItem(BaseModel):
    name: str = Field(min_length=1)
    quantity: int = Field(ge=0)


class BankUpdateRequest(BaseModel):
    stocks: list[StockItem]


class TradeRequest(BaseModel):
    type: Literal["buy", "sell"]