"""Discovery source registry."""

from scrapper.discovery.sources.fake_source import FakeSource

SOURCES: dict[str, type] = {
    "fake": FakeSource,
}
