import datetime
import decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, root_validator


class BaseSchema(BaseModel):
    class Config:
        orm_mode = True
        use_enum_values = True
        json_encoders = {
            datetime.time: lambda v: v.strftime("%H:%M"),
        }


class FinancialData(BaseSchema):
    symbol: str
    date: datetime.date
    open_price: decimal.Decimal
    close_price: decimal.Decimal
    volume: int


class FinancialDataCreate(FinancialData):
    open_price: decimal.Decimal = Field(..., alias="1. open")
    close_price: decimal.Decimal = Field(..., alias="4. close")
    volume: int = Field(..., alias="6. volume")


class Pagination(BaseSchema):
    count: int
    page: int
    limit: int
    pages: int


class Info(BaseSchema):
    error: str


class FinancialDataResponse(BaseSchema):
    data: Optional[List[FinancialData]]
    pagination: Optional[Pagination]
    info: Info


class FinancialDataStats(BaseSchema):
    start_date: datetime.date
    end_date: datetime.date
    symbol: str
    average_daily_open_price: Optional[decimal.Decimal]
    average_daily_close_price: Optional[decimal.Decimal]
    average_daily_volume: Optional[decimal.Decimal]


class StatsResponse(BaseSchema):
    data: Optional[FinancialDataStats]
    info: Info


class FinancialDataFilters(BaseSchema):
    symbol: Optional[str] = None
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None

    @root_validator
    def check_interval(cls, values: dict) -> dict:  # pylint: disable=no-self-argument
        """
        Checks if both dates are not None than end_date must come after start_date
        """
        start_date = values.get("start_date")
        end_date = values.get("end_date")

        if start_date and end_date and start_date >= end_date:
            raise ValueError("Field end_date must come after start_date")

        return values

    def make_filters(self) -> Optional[Dict[str, Any]]:
        filters: Dict[str, Any] = {}

        if self.symbol is not None:
            filters["symbol"] = self.symbol

        if self.start_date is not None:
            filters["date__ge"] = self.start_date

        if self.end_date is not None:
            filters["date__le"] = self.end_date

        return filters or None


class StatisticsFilters(FinancialDataFilters):
    symbol: str
    start_date: datetime.date
    end_date: datetime.date


class PaginationFilters(BaseSchema):  # pylint: disable=C0115
    page: Optional[int] = Field(default=1, ge=1)
    limit: Optional[int] = Field(default=5, le=100)
