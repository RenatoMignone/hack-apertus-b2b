"""Manually entered plans, never model-extracted facts or economic forecasts."""
from decimal import Decimal
from pydantic import Field, model_validator
from backend.contracts.data import Contract


class BusinessContext(Contract):
    planned_jobs: int | None = Field(default=None, ge=0, le=1_000_000, strict=True)
    investment_amount: Decimal | None = Field(default=None, ge=0, max_digits=20, decimal_places=2)
    investment_currency: str | None = Field(default=None, pattern=r'^[A-Z]{3}$',
        description='Explicit three-letter currency code; no currency inference or conversion')
    timeline: str | None = Field(default=None, min_length=1, max_length=500)

    @model_validator(mode='after')
    def paired_amount_currency(self):
        if (self.investment_amount is None) != (self.investment_currency is None):
            raise ValueError('investment needs both amount and currency')
        return self

    def lines(self):
        result = []
        if self.planned_jobs is not None:
            result.append(f'Planned jobs: {self.planned_jobs}')
        if self.investment_amount is not None:
            result.append(f'Planned investment: {self.investment_amount} {self.investment_currency}')
        if self.timeline:
            result.append(f'Planned timeline: {self.timeline}')
        return result
