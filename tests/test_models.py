"""Tests for data models."""

from scrapper.db.models import CandidateHint, Lead


class TestCandidateHint:
    def test_create(self):
        hint = CandidateHint(company_name="ООО Тест", source="fake")
        assert hint.company_name == "ООО Тест"
        assert hint.source == "fake"
        assert hint.metadata == {}

    def test_with_metadata(self):
        hint = CandidateHint(
            company_name="Test", source="api", metadata={"region": "Москва"}
        )
        assert hint.metadata["region"] == "Москва"


class TestLead:
    def test_create_minimal(self):
        lead = Lead(task_id=1, company_name="ООО Тест")
        assert lead.task_id == 1
        assert lead.inn is None

    def test_create_full(self):
        lead = Lead(
            task_id=1,
            company_name="ООО Тест",
            inn="7701234567",
            ogrn="1027700000001",
            phone="+74951234567",
            email="test@test.ru",
        )
        assert lead.inn == "7701234567"
        assert lead.email == "test@test.ru"
