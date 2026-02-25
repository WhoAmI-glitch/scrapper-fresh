"""Discovery source registry."""

from scrapper.discovery.sources.fake_source import FakeSource
from scrapper.discovery.sources.twogis import TwoGisSource
from scrapper.discovery.sources.yandex_maps import YandexMapsSource
from scrapper.discovery.sources.zakupki import ZakupkiSource

SOURCES: dict[str, type] = {
    "fake": FakeSource,
    "yandex_maps": YandexMapsSource,
    "twogis": TwoGisSource,
    "zakupki": ZakupkiSource,
}
