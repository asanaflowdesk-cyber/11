from __future__ import annotations

from urllib.parse import quote_plus

from .normalization import clean_text


def make_search_query(bin_number: str, company_name: str | None, address: str | None = None) -> str:
    parts = [clean_text(bin_number), clean_text(company_name), clean_text(address)]
    return " ".join([p for p in parts if p])


def dgis_search_url(query: str) -> str:
    return "https://2gis.kz/search/" + quote_plus(query)


def google_search_url(query: str) -> str:
    return "https://www.google.com/search?q=" + quote_plus(query + " телефон контакты")


def yandex_search_url(query: str) -> str:
    return "https://yandex.kz/search/?text=" + quote_plus(query + " телефон контакты")
