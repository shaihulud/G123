import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from financial.apps.financial import schemas
from financial.apps.financial.models import FinancialData
from financial.deps import get_db


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/financial_data", response_model=schemas.FinancialDataResponse)
async def get_financial_data(
    db: AsyncSession = Depends(get_db),
    filters: schemas.FinancialDataFilters = Depends(),
    pagination: schemas.PaginationFilters = Depends(),
) -> Any:
    """
    For the user specified period and symbol retrieves daily records
    with daily open price, daily closing price and daily volume.
    """
    data, count, pages = await FinancialData.paginate(
        db, filters=filters.make_filters(), sorting={"date": "asc"}, page=pagination.page, per_page=pagination.limit
    )
    return {
        "data": data,
        "pagination": {"count": count, "page": pagination.page, "limit": pagination.limit, "pages": pages},
        "info": {"error": ""},
    }


@router.get("/statistics", response_model=schemas.StatsResponse)
async def get_statistics(db: AsyncSession = Depends(get_db), filters: schemas.StatisticsFilters = Depends()) -> Any:
    """
    For the user specified period and symbol calculates the average daily open price,
    the average daily closing price and the average daily volume.
    """
    result = await FinancialData.count_stats(db, filters.make_filters())  # type: ignore
    data = filters.dict()
    data.update(result)
    return {"data": data, "info": {"error": ""}}
