import asyncio
from datetime import datetime, timezone
from decimal import Decimal
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Override settings before app imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["API_KEY"] = "test-api-key-12345"

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models.trader import TraderProfile
from app.models.session import TradingSession, SessionStatus

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session
        await db_session.commit()

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest_asyncio.fixture(scope="function")
async def sample_trader(db_session: AsyncSession) -> TraderProfile:
    trader = TraderProfile(
        external_id="test_trader_001",
        display_name="Test Trader",
        default_position_limit=Decimal("500.00"),
        daily_loss_limit=Decimal("5000.00"),
        is_synthetic=True
    )
    db_session.add(trader)
    await db_session.commit()
    await db_session.refresh(trader)
    return trader

@pytest_asyncio.fixture(scope="function")
async def sample_session(db_session: AsyncSession, sample_trader: TraderProfile) -> TradingSession:
    sess = TradingSession(
        trader_id=sample_trader.id,
        scenario_id="test_scenario",
        status=SessionStatus.ACTIVE,
        peak_pnl=Decimal("0.00"),
        current_pnl=Decimal("0.00"),
        total_trades=0,
        is_synthetic=True
    )
    db_session.add(sess)
    await db_session.commit()
    await db_session.refresh(sess)
    return sess
