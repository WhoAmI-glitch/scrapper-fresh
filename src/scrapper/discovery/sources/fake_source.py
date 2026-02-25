"""Fake discovery source with demo Russian construction companies."""

from __future__ import annotations

from typing import TYPE_CHECKING

from scrapper.db.models import CandidateHint
from scrapper.discovery.base import DiscoverySource

if TYPE_CHECKING:
    from collections.abc import Iterator


class FakeSource(DiscoverySource):
    """Demo source that yields 8 realistic Russian construction companies.

    Useful for development, testing, and pipeline verification
    without hitting real external APIs.
    """

    def __init__(self) -> None:
        super().__init__(source_name="fake")

    def discover(self) -> Iterator[CandidateHint]:
        companies = [
            ("ООО СтройГарант", "Строительные материалы, Москва"),
            ("АО Бетон-Сервис", "Производство бетона, Санкт-Петербург"),
            ("ООО КровляМонтаж", "Кровельные работы, Новосибирск"),
            ("ИП Козлов А.В.", "Сантехника оптом, Екатеринбург"),
            ("ООО ТеплоСтрой", "Утепление фасадов, Казань"),
            ("ПАО СибирьЦемент", "Цементный завод, Красноярск"),
            ("ООО Фасад-Плюс", "Фасадные материалы, Нижний Новгород"),
            ("ЗАО МосСтройКомплект", "Комплексные поставки, Москва"),
        ]
        for name, hint in companies:
            yield CandidateHint(
                company_name=name,
                source=self.source_name,
                hint_text=hint,
            )
