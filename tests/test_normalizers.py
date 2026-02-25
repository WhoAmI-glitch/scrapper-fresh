"""Tests for Russian-market data normalizers."""


from scrapper.normalizers import (
    clean_company_name,
    clean_text,
    normalize_inn,
    normalize_ogrn,
    normalize_phone,
    validate_inn_checksum,
)


class TestNormalizePhone:
    def test_standard_mobile(self):
        assert normalize_phone("+7 (916) 123-45-67") == "+79161234567"

    def test_eight_prefix(self):
        assert normalize_phone("8 (495) 123-45-67") == "+74951234567"

    def test_seven_prefix(self):
        assert normalize_phone("7 495 123 45 67") == "+74951234567"

    def test_raw_digits_11(self):
        assert normalize_phone("89161234567") == "+79161234567"

    def test_raw_digits_10(self):
        assert normalize_phone("9161234567") == "+79161234567"

    def test_with_dashes_and_parens(self):
        assert normalize_phone("+7(495)123-45-67") == "+74951234567"

    def test_too_short(self):
        assert normalize_phone("12345") is None

    def test_empty(self):
        assert normalize_phone("") is None

    def test_none_input(self):
        assert normalize_phone(None) is None

    def test_international_non_ru(self):
        # Non-Russian numbers should return None or the normalized form
        result = normalize_phone("+1 555 123 4567")
        assert result is None  # Only handles RU phones


class TestNormalizeInn:
    def test_valid_10_digit(self):
        assert normalize_inn("7701234567") == "7701234567"

    def test_valid_12_digit(self):
        assert normalize_inn("770123456789") == "770123456789"

    def test_strips_whitespace(self):
        assert normalize_inn(" 7701234567 ") == "7701234567"

    def test_invalid_length(self):
        assert normalize_inn("12345") is None

    def test_non_digits(self):
        assert normalize_inn("77012ABC67") is None

    def test_empty(self):
        assert normalize_inn("") is None

    def test_none(self):
        assert normalize_inn(None) is None


class TestNormalizeOgrn:
    def test_valid_13_digit(self):
        assert normalize_ogrn("1027700000001") == "1027700000001"

    def test_valid_15_digit(self):
        assert normalize_ogrn("304770000000001") == "304770000000001"

    def test_strips_whitespace(self):
        assert normalize_ogrn("  1027700000001  ") == "1027700000001"

    def test_invalid(self):
        assert normalize_ogrn("12345") is None

    def test_none(self):
        assert normalize_ogrn(None) is None


class TestCleanCompanyName:
    def test_strip_ooo(self):
        assert clean_company_name('ООО "СтройГарант"') == "СтройГарант"

    def test_strip_oao(self):
        assert clean_company_name("ОАО Бетон-Сервис") == "Бетон-Сервис"

    def test_strip_zao(self):
        assert clean_company_name("ЗАО МосСтройКомплект") == "МосСтройКомплект"

    def test_strip_pao(self):
        assert clean_company_name("ПАО СибирьЦемент") == "СибирьЦемент"

    def test_strip_ip(self):
        result = clean_company_name("ИП Козлов А.В.")
        assert "ИП" not in result
        assert "Козлов" in result

    def test_strip_ao(self):
        assert clean_company_name("АО Ромашка") == "Ромашка"

    def test_normalize_quotes(self):
        result = clean_company_name('ООО «Тест»')
        assert "ООО" not in result
        assert "Тест" in result

    def test_preserve_content(self):
        assert clean_company_name("СтройГарант") == "СтройГарант"

    def test_empty(self):
        assert clean_company_name("") == ""


class TestCleanText:
    def test_strips_nbsp(self):
        assert clean_text("hello\xa0world") == "hello world"

    def test_strips_multiple_spaces(self):
        assert clean_text("hello   world") == "hello world"

    def test_strips_leading_trailing(self):
        assert clean_text("  hello  ") == "hello"

    def test_strips_newlines(self):
        assert clean_text("hello\n\nworld") == "hello world"

    def test_empty(self):
        assert clean_text("") == ""

    def test_none(self):
        assert clean_text(None) == ""


class TestValidateInnChecksum:
    def test_valid_10_digit(self):
        # Using known valid INN: 7707083893 (Сбербанк)
        assert validate_inn_checksum("7707083893") is True

    def test_valid_12_digit(self):
        # Using known valid 12-digit INN: 500100732259
        assert validate_inn_checksum("500100732259") is True

    def test_invalid_10_digit(self):
        assert validate_inn_checksum("7707083890") is False

    def test_wrong_length(self):
        assert validate_inn_checksum("12345") is False

    def test_empty(self):
        assert validate_inn_checksum("") is False
