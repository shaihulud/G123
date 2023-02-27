from typing import Any, Dict

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from financial.config import settings
from financial.db import EmptyBaseModel


class FinancialData(EmptyBaseModel):
    __tablename__ = "financial_data"

    id = sa.Column(sa.Integer, primary_key=True)
    symbol = sa.Column(sa.String(settings.MAX_SYMBOL_LENGTH), nullable=False)
    date = sa.Column(sa.Date, nullable=False)
    # Use decimal because floats and doubles don't have an accurate enough representation
    # to prevent rounding errors from accumulating when doing arithmetic with monetary values
    open_price = sa.Column(sa.DECIMAL, nullable=False)
    close_price = sa.Column(sa.DECIMAL, nullable=False)
    volume = sa.Column(sa.BigInteger, nullable=False)

    # This pair must be unique through the DB. Also it helps to use Postgres ON CONFLICT statement.
    __table_args__ = (sa.Index("ix_symbol_date", "symbol", "date", unique=True),)

    @classmethod
    async def count_stats(cls, session: AsyncSession, filters: Dict[str, Any]) -> dict:
        """
        Returns average for open_price, close_price and volume with conditions from filters.
        """
        query = sa.select(
            [
                sa.func.avg(cls.open_price).label("average_daily_open_price"),
                sa.func.avg(cls.close_price).label("average_daily_close_price"),
                sa.func.avg(cls.volume).label("average_daily_volume"),
            ]
        ).where(sa.and_(True, *cls.build_filters(filters)))
        db_execute = await session.execute(query)
        result = db_execute.mappings().fetchone()
        return result
