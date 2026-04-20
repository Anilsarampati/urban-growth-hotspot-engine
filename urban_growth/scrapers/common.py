from __future__ import annotations

import re
from typing import Iterable

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def build_session() -> requests.Session:
    retry = Retry(
        total=3,
        backoff_factor=0.8,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def to_float(value: str) -> float | None:
    cleaned = re.sub(r"[^\d.\-]", "", value)
    if cleaned in {"", ".", "-", "-."}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def first_not_none(values: Iterable[float | None], fallback: float) -> float:
    for value in values:
        if value is not None:
            return value
    return fallback
