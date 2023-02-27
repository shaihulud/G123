import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from financial.deps import get_db


logger = logging.getLogger(__name__)
router = APIRouter()


class InternalServerError(Exception):
    """HTTP 500"""


class ProbeError(Exception):
    """HTTP 503"""


async def db_check(db: AsyncSession) -> None:
    try:
        await db.scalar(text("SELECT 1"))
    except Exception as e:
        logger.error("Service health-check error: %s", e)
        raise ProbeError from e


@router.get("/livez")
async def liveness_probe():
    return "OK"


@router.get("/healthz")
async def readiness_probe(db: AsyncSession = Depends(get_db)) -> str:
    await db_check(db)
    return "OK"
