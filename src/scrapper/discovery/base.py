"""Abstract base class for discovery sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from scrapper.db.models import CandidateHint


class DiscoverySource(ABC):
    """Base class for all discovery sources.

    Each source has a unique name and yields CandidateHint objects
    representing companies found during discovery.
    """

    def __init__(self, source_name: str) -> None:
        self.source_name = source_name

    @abstractmethod
    def discover(self) -> Iterator[CandidateHint]:
        """Yield company candidates from this source."""
        ...
