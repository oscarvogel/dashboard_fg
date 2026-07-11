from dataclasses import dataclass
import re
import unicodedata

from django.core.exceptions import ValidationError


MAX_ALIAS_LENGTH = 120
_UNICODE_DASHES = dict.fromkeys(
    map(ord, "\u058a\u05be\u1400\u1806\u2010\u2011\u2012\u2013\u2014\u2015\u2e17\u2e1a\u2e3a\u2e3b\u2e40\u301c\u3030\u30a0\ufe31\ufe32\ufe58\ufe63\uff0d"),
    "-",
)
_SEPARATORS = re.compile(r"[\s-]+")
_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class NormalizedAlias:
    display: str
    normalized: str


def normalize_alias(value):
    if not isinstance(value, str):
        raise ValidationError("El alias debe ser texto")

    display = unicodedata.normalize("NFKC", value).translate(_UNICODE_DASHES)
    display = _WHITESPACE.sub(" ", display).strip()
    if not display:
        raise ValidationError("El alias no puede estar vacío")
    if len(display) > MAX_ALIAS_LENGTH:
        raise ValidationError(
            f"El alias no puede superar {MAX_ALIAS_LENGTH} caracteres"
        )

    comparable = unicodedata.normalize("NFKD", display.casefold())
    comparable = "".join(
        character
        for character in comparable
        if unicodedata.category(character) != "Mn"
    )
    normalized = _SEPARATORS.sub("", comparable)
    if not normalized:
        raise ValidationError("El alias no puede estar vacío")

    return NormalizedAlias(display=display, normalized=normalized)
