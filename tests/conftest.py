import asyncio

import pytest
from httpx import AsyncClient
from sqlalchemy import event
from sqlalchemy.engine import Transaction
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from financial.db import engine
from financial.deps import get_db
from financial.main import app


@pytest.fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def db_engine():
    return engine


@pytest.fixture
async def client(db: AsyncSession):
    def _get_db():
        return db

    app.dependency_overrides[get_db] = _get_db
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def db(db_engine):
    """Fixture of SQLAlchemy session object with auto rollback after each test case"""
    # https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
    connection = await db_engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False, future=True, autoflush=False)
    await connection.begin_nested()

    @event.listens_for(session.sync_session, "after_transaction_end")
    def end_savepoint(session: Session, transaction: Transaction) -> None:
        """async events are not implemented yet, recreates savepoints to avoid final commits"""
        # https://github.com/sqlalchemy/sqlalchemy/issues/5811#issuecomment-756269881
        if connection.closed:
            return
        if not connection.in_nested_transaction():
            connection.sync_connection.begin_nested()

    yield session
    if session.in_transaction():  # pylint: disable=no-member
        await transaction.rollback()
    await connection.close()
