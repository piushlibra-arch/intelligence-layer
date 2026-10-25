from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import uuid
from typing import NamedTuple
from app.models.event import EventType
from app.schemas.events import EventIngestRequest

class ScenarioTraderConfig(NamedTuple):
    external_id: str
    display_name: str
    historical_sessions_count: int
    default_position_limit: Decimal
    daily_loss_limit: Decimal
    baseline_reentry: Decimal | None
    baseline_position: Decimal | None
    baseline_frequency: Decimal | None

class BaseScenario(ABC):
    @property
    @abstractmethod
    def scenario_id(self) -> str:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def expected_outcome(self) -> str:
        pass

    @property
    @abstractmethod
    def trader_config(self) -> ScenarioTraderConfig:
        pass

    @abstractmethod
    def generate_events(self, base_time: datetime | None = None) -> list[EventIngestRequest]:
        pass
