"""Discovery source registry."""

from scrapper.discovery.sources.fake_source import FakeSource
from scrapper.discovery.sources.yandex_maps import YandexMapsSource

SOURCES: dict[str, type] = {
    "fake": FakeSource,
    "yandex_maps": YandexMapsSource,
}
