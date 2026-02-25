"""Text normalization utilities for Russian-market data.

Handles phone numbers, INN/OGRN validation, company name cleaning,
and general text sanitization.
"""

from __future__ import annotations

import re


def normalize_phone(raw: str | None) -> str | None:
    """Normalize a Russian phone number to +7XXXXXXXXXX format.

    Handles 8-prefix (8-800, 8-495, etc.) and +7 prefix.
    Returns None if input is None or cannot be parsed as a valid RU phone.
    """
    if raw is None:
        return None

    # Strip everything except digits and leading +
    cleaned = re.sub(r"[^\d+]", "", raw)

    # Remove leading +
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]

    # Must start with 7 or 8 for Russian numbers
    if cleaned.startswith("8") and len(cleaned) == 11:
        cleaned = "7" + cleaned[1:]
    elif cleaned.startswith("7") and len(cleaned) == 11:
        pass  # already correct
    elif len(cleaned) == 10:
        # Assume missing country code
        cleaned = "7" + cleaned
    else:
        return None

    if len(cleaned) != 11:
        return None

    return f"+{cleaned}"


def validate_inn_checksum(inn: str) -> bool:
    """Validate the checksum of a Russian INN (10 or 12 digits).

    10-digit INN (legal entities): one check digit (position 10).
    12-digit INN (individuals): two check digits (positions 11 and 12).

    Returns False if the INN is not 10 or 12 digits, or if checksum fails.
    """
    if inn is None or not inn.isdigit():
        return False

    digits = [int(d) for d in inn]

    if len(digits) == 10:
        weights = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        check = sum(w * d for w, d in zip(weights, digits[:9], strict=True)) % 11 % 10
        return check == digits[9]

    elif len(digits) == 12:
        # First check digit (position 11)
        weights_11 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        check_11 = sum(w * d for w, d in zip(weights_11, digits[:10], strict=True)) % 11 % 10
        if check_11 != digits[10]:
            return False

        # Second check digit (position 12)
        weights_12 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        check_12 = sum(w * d for w, d in zip(weights_12, digits[:11], strict=True)) % 11 % 10
        return check_12 == digits[11]

    return False


def normalize_inn(raw: str | None) -> str | None:
    """Normalize a Russian INN: strip whitespace, validate format (10 or 12 digits).

    Does NOT validate checksum — use validate_inn_checksum() for that.
    Returns None if input is None, non-numeric, or wrong length.
    """
    if raw is None:
        return None

    cleaned = re.sub(r"\s+", "", raw).strip()

    if not cleaned.isdigit():
        return None

    if len(cleaned) not in (10, 12):
        return None

    return cleaned


def normalize_ogrn(raw: str | None) -> str | None:
    """Normalize and validate a Russian OGRN/OGRNIP.

    Strips whitespace, validates length (13 digits for OGRN,
    15 digits for OGRNIP). Returns None on invalid input.
    """
    if raw is None:
        return None

    cleaned = re.sub(r"\s+", "", raw).strip()

    if not cleaned.isdigit():
        return None

    if len(cleaned) not in (13, 15):
        return None

    return cleaned


# Legal form prefixes to strip from company names
_LEGAL_FORMS = [
    "ООО",
    "ОАО",
    "ЗАО",
    "ПАО",
    "АО",
    "ИП",
]

# Build a regex pattern that matches legal forms at the start of a name,
# optionally surrounded by quotes
_LEGAL_FORMS_PATTERN = re.compile(
    r"^(?:" + "|".join(re.escape(f) for f in _LEGAL_FORMS) + r")\s*",
    re.IGNORECASE,
)


def clean_company_name(raw: str | None) -> str:
    """Clean a company name by removing legal form prefixes and normalizing.

    Strips legal forms (ООО, ОАО, ЗАО, ПАО, АО, ИП), removes surrounding
    quotes, and normalizes whitespace.

    Returns empty string if input is None.
    """
    if raw is None:
        return ""

    name = raw.strip()

    # Remove surrounding quotes (various styles)
    name = re.sub(r'^[«"\']+', "", name)
    name = re.sub(r'[»"\']+$', "", name)

    # Remove legal form prefix
    name = _LEGAL_FORMS_PATTERN.sub("", name).strip()

    # Remove quotes again in case they wrapped the name after the legal form
    name = re.sub(r'^[«"\']+', "", name)
    name = re.sub(r'[»"\']+$', "", name)

    # Normalize whitespace
    name = re.sub(r"\s+", " ", name).strip()

    return name


def clean_text(raw: str | None) -> str:
    """Clean arbitrary text: strip nbsp, normalize whitespace.

    Returns empty string if input is None.
    """
    if raw is None:
        return ""

    text = raw.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text
