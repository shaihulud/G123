import asyncio
import logging
from datetime import timedelta
from json import JSONDecodeError
from typing import List

import httpx
from fastapi import status
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from financial.apps.financial import models, schemas
from financial.config import settings
from financial.db import async_session
from financial.utils import utcnow


URL = "https://www.alphavantage.co/query"
PARAMS = {
    "function": "TIME_SERIES_DAILY_ADJUSTED",
    "apikey": settings.ALPHAVANTAGE_APIKEY,
}

logger = logging.getLogger(__name__)


async def get_symbol_history(symbol: str) -> dict:
    """
    Returns alphavantage raw (as-traded) daily open/high/low/close/volume values,
    daily adjusted close values, and historical split/dividend events of the
    specified symbol.

    !!! By default it returns only latest 100 data points. If date is less than minimal
    date in response, we need to add request parameter outputsize=full. But I won't do
    this because in test assignment we need only 2 last weeks !!!

    https://www.alphavantage.co/documentation/#dailyadj
    """
    params = {"symbol": symbol}
    params.update(PARAMS)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(URL, params=params)
    except httpx.RequestError:
        logger.exception("Exception while getting symbol history")
        return {}

    if response.status_code != status.HTTP_200_OK:
        logger.error("Error: alphavantage respond with status %s: %s", response.status_code, response.text)
        return {}

    try:
        data = response.json()
    except (TypeError, ValueError, JSONDecodeError):
        logger.error("Error: alphavantage respond with wrong data: %s", response.text)
        return {}

    if "Time Series (Daily)" not in data:
        logger.error("Error: alphavantage respond with wrong data: %s", response.text)
        return {}

    return data["Time Series (Daily)"]


def get_days_list() -> List[str]:
    """Returns list of days in isoformat from today to ALPHAVANTAGE_LAST_DAYS back in history."""
    today = utcnow().date()
    days_list = [today.isoformat()]

    for i in range(1, settings.ALPHAVANTAGE_LAST_DAYS):
        date_str = (today - timedelta(days=i)).isoformat()
        days_list.append(date_str)

    return days_list


async def fill_financial_data() -> None:
    """
    Populates financial_data table with new data collected from alphavantage.

    Makes request to alphavantage API to collect stock data for ALPHAVANTAGE_SYMBOLS.
    Parses response and returns stock history for the last ALPHAVANTAGE_LAST_DAYS days.
    Upserts collected data to database.
    """
    # This is made because prepare 14 days to get them from history is faster,
    # then parse every date in history and compare it with today-14
    days_list = get_days_list()

    # If there would be many symbols, it would be a bad idea to get them all simultaneously - we could be
    # banned or throttled. For this case it must be batched with sleeps between batches depending on throttling policy.
    symbols_history = await asyncio.gather(*[get_symbol_history(symbol) for symbol in settings.ALPHAVANTAGE_SYMBOLS])

    for symbol, history in zip(settings.ALPHAVANTAGE_SYMBOLS, symbols_history):
        if not history:
            continue

        objects = []

        for day in days_list:
            raw_obj = history.get(day)
            if raw_obj:
                raw_obj["symbol"] = symbol
                raw_obj["date"] = day

                try:
                    obj = schemas.FinancialDataCreate.parse_obj(raw_obj)
                except ValidationError:
                    logger.exception("Error while parsing alphavantage object data.")
                    continue

                objects.append(obj)

        # In test assignment description it's written to use upsert operation. If data does not change over time I'd
        # rather check which dates are not in DB and insert them in bulk - it's much faster. But I will use upsert
        # here as it is a requirement if I understand the task correctly.
        await asyncio.gather(*[upsert(obj) for obj in objects])


async def upsert(obj: schemas.FinancialDataCreate) -> None:
    try:
        async with async_session() as session:
            ids = {"symbol": obj.symbol, "date": obj.date}
            await models.FinancialData.insert_or_update(session, ids, obj.dict())
            await session.commit()
    except SQLAlchemyError:
        logger.exception("Exception occurred while saving financial data to database.")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(fill_financial_data())
