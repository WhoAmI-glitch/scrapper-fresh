"""AIS data provider client with support for MarineTraffic and mock backends.

The provider is selected via the TRACKER_AIS_PROVIDER environment variable.
In development, the mock provider returns randomised positions near each
vessel's last known position, enabling end-to-end testing without API costs.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from loguru import logger

from tracker.config import get_settings


@dataclass(frozen=True)
class VesselPosition:
    """Immutable container for a vessel position report."""

    imo_number: str
    lat: float
    lon: float
    speed: float
    heading: float
    timestamp: datetime


class AISProvider(ABC):
    """Abstract base class for AIS data providers."""

    @abstractmethod
    async def get_vessel_position(self, imo_or_mmsi: str) -> VesselPosition | None:
        """Fetch the latest position for a single vessel by IMO or MMSI."""
        ...

    @abstractmethod
    async def get_vessel_positions_batch(
        self, imo_list: list[str]
    ) -> list[VesselPosition]:
        """Fetch latest positions for multiple vessels at once."""
        ...


class MarineTrafficProvider(AISProvider):
    """AIS data provider using the MarineTraffic API.

    Requires a valid API key with vessel tracking permissions.
    See: https://www.marinetraffic.com/en/ais-api-services
    """

    def __init__(self, api_key: str, base_url: str) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=30.0)

    async def get_vessel_position(self, imo_or_mmsi: str) -> VesselPosition | None:
        """Fetch position from MarineTraffic PS07 (single vessel) endpoint."""
        url = (
            f"{self._base_url}"
            f"/{self._api_key}"
            f"/imo:{imo_or_mmsi}"
            f"/msgtype:simple"
            f"/protocol:jsono"
        )
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            data = response.json()

            if not data or not isinstance(data, list) or len(data) == 0:
                logger.warning("No AIS data returned for {}", imo_or_mmsi)
                return None

            record = data[0]
            return VesselPosition(
                imo_number=imo_or_mmsi,
                lat=float(record.get("LAT", 0)),
                lon=float(record.get("LON", 0)),
                speed=float(record.get("SPEED", 0)) / 10.0,  # MT returns speed * 10
                heading=float(record.get("HEADING", 0)),
                timestamp=datetime.fromisoformat(
                    record.get("TIMESTAMP", datetime.now(timezone.utc).isoformat())
                ),
            )
        except httpx.HTTPStatusError as exc:
            logger.error(
                "MarineTraffic API error for {}: {} {}",
                imo_or_mmsi,
                exc.response.status_code,
                exc.response.text[:200],
            )
            return None
        except Exception as exc:
            logger.error("Failed to fetch AIS data for {}: {}", imo_or_mmsi, exc)
            return None

    async def get_vessel_positions_batch(
        self, imo_list: list[str]
    ) -> list[VesselPosition]:
        """Fetch positions for multiple vessels sequentially.

        MarineTraffic does not have a true batch endpoint for the basic
        tier, so we iterate. For production with many vessels, upgrade
        to a streaming/fleet endpoint.
        """
        positions: list[VesselPosition] = []
        for imo in imo_list:
            pos = await self.get_vessel_position(imo)
            if pos is not None:
                positions.append(pos)
        return positions

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()


class MockAISProvider(AISProvider):
    """Mock AIS provider for development and testing.

    Generates slightly randomised positions that simulate vessel movement.
    Positions drift a small amount on each call, simulating a vessel
    travelling at roughly 10-12 knots.
    """

    def __init__(self) -> None:
        # Cache of last-known positions for drift simulation
        self._positions: dict[str, tuple[float, float, float, float]] = {}

    async def get_vessel_position(self, imo_or_mmsi: str) -> VesselPosition | None:
        """Generate a mock position with small random drift."""
        if imo_or_mmsi in self._positions:
            lat, lon, speed, heading = self._positions[imo_or_mmsi]
        else:
            # Default position in mid-Atlantic if we have no prior data
            lat = random.uniform(-10.0, 10.0)
            lon = random.uniform(-30.0, 10.0)
            speed = random.uniform(9.0, 13.0)
            heading = random.uniform(0.0, 360.0)

        # Simulate drift: ~0.01 degrees per poll (~5 min at ~12 knots)
        lat += random.uniform(-0.02, 0.02)
        lon += random.uniform(-0.02, 0.02)
        speed = max(0.0, speed + random.uniform(-0.5, 0.5))
        heading = (heading + random.uniform(-5.0, 5.0)) % 360.0

        # Clamp to valid ranges
        lat = max(-90.0, min(90.0, lat))
        lon = max(-180.0, min(180.0, lon))

        self._positions[imo_or_mmsi] = (lat, lon, speed, heading)

        return VesselPosition(
            imo_number=imo_or_mmsi,
            lat=round(lat, 6),
            lon=round(lon, 6),
            speed=round(speed, 1),
            heading=round(heading, 1),
            timestamp=datetime.now(timezone.utc),
        )

    async def get_vessel_positions_batch(
        self, imo_list: list[str]
    ) -> list[VesselPosition]:
        """Fetch mock positions for all requested vessels."""
        positions: list[VesselPosition] = []
        for imo in imo_list:
            pos = await self.get_vessel_position(imo)
            if pos is not None:
                positions.append(pos)
        return positions

    def seed_position(
        self, imo: str, lat: float, lon: float, speed: float, heading: float
    ) -> None:
        """Pre-seed a known position for a vessel (useful for tests)."""
        self._positions[imo] = (lat, lon, speed, heading)


def create_ais_provider() -> AISProvider:
    """Factory that returns the configured AIS provider.

    Set TRACKER_AIS_PROVIDER to 'marinetraffic' for production,
    or 'mock' (default) for development.
    """
    settings = get_settings()

    if settings.ais_provider == "marinetraffic":
        if not settings.ais_api_key:
            raise ValueError(
                "TRACKER_AIS_API_KEY must be set when using the marinetraffic provider"
            )
        logger.info("Using MarineTraffic AIS provider")
        return MarineTrafficProvider(
            api_key=settings.ais_api_key,
            base_url=settings.ais_base_url,
        )

    logger.info("Using mock AIS provider (set TRACKER_AIS_PROVIDER=marinetraffic for production)")
    return MockAISProvider()
