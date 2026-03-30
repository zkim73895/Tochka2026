from typing import Optional

from pydantic import BaseModel, conint, constr, field_validator


class TicketDraft(BaseModel):
    direction: str
    ticker: constr(min_length=2, max_length=10, pattern="^[A-Z]+$")
    qty: conint(gt=0)
    price: Optional[conint(gt=0)] = None

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, value: str) -> str:
        expected = ["BUY", "SELL"]
        if value not in expected:
            raise ValueError(f"Direction must be enum {expected}")
        return value

