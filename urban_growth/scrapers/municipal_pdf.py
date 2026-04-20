from __future__ import annotations

from io import BytesIO
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import pandas as pd
from pypdf import PdfReader

from .common import build_session, clean_text, first_not_none, to_float


@dataclass
class MunicipalPdfRecord:
    city: str
    zone: str
    lat: float
    lon: float
    declaration_type: str
    announced_date: str
    infra_impact_score: float
    source_url: str


DECLARATION_KEYWORDS = {
    "tender": 92.0,
    "road": 90.0,
    "metro": 95.0,
    "sewer": 84.0,
    "sewage": 84.0,
    "drain": 78.0,
    "drainage": 78.0,
    "water": 80.0,
    "zoning": 88.0,
    "land use": 89.0,
    "policy": 85.0,
    "notice": 76.0,
    "notification": 76.0,
    "ward": 70.0,
}


def scrape_municipal_pdf_portals(urls: list[str], default_city: str = "default") -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    session = build_session()

    for url in urls:
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
        except Exception:
            continue

        reader = PdfReader(BytesIO(response.content))
        text = _extract_pdf_text(reader)
        if not text:
            continue

        record = _parse_pdf_text(text, url, default_city)
        if record is not None:
            rows.append(record)

    if not rows:
        return pd.DataFrame(
            columns=[
                "city",
                "zone",
                "lat",
                "lon",
                "declaration_type",
                "announced_date",
                "infra_impact_score",
            ]
        )

    return pd.DataFrame(rows)


def _extract_pdf_text(reader: PdfReader) -> str:
    pages: list[str] = []
    for page in reader.pages:
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""
        if page_text:
            pages.append(page_text)
    return clean_text(" \n".join(pages))


def _parse_pdf_text(text: str, source_url: str, default_city: str) -> dict[str, object] | None:
    lowered = text.lower()
    declaration_type = _infer_declaration_type(lowered)
    zone = _infer_zone(text) or _infer_zone_from_url(source_url) or "Municipal Zone"
    city = _infer_city(text, source_url, default_city)
    announced_date = _infer_date(text)
    infra_score = _infer_impact_score(lowered)
    lat, lon = _infer_coordinates(text)

    return {
        "city": city,
        "zone": zone,
        "lat": lat,
        "lon": lon,
        "declaration_type": declaration_type,
        "announced_date": announced_date,
        "infra_impact_score": infra_score,
        "source_url": source_url,
    }


def _infer_declaration_type(text: str) -> str:
    for keyword in ["metro", "road", "sewage", "drainage", "policy", "zoning", "tender", "notification", "notice"]:
        if keyword in text:
            return keyword.title() if keyword != "zoning" else "Land Use Change"
    return "Municipal Declaration"


def _infer_zone(text: str) -> str | None:
    patterns = [
        r"ward\s*no\.?\s*(\d+[a-z]?)",
        r"zone\s*([a-z])",
        r"sector\s*(\d+[a-z]?)",
        r"locality\s*[:\-]\s*([A-Za-z0-9 &\-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = clean_text(match.group(1))
            return f"Ward {value}" if pattern.startswith("ward") else value
    return None


def _infer_zone_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    if not parsed.path:
        return None
    slug = parsed.path.split("/")[-1].replace(".pdf", "")
    slug = clean_text(slug.replace("-", " ").replace("_", " "))
    return slug.title() if slug else None


def _infer_city(text: str, source_url: str, default_city: str) -> str:
    lowered = f"{text.lower()} {source_url.lower()}"
    if any(keyword in lowered for keyword in ["delhi", "mcd", "ndmc", "ncr"]):
        return "Delhi NCR"
    if "pune" in lowered:
        return "Pune"
    return default_city


def _infer_date(text: str) -> str:
    match = re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", text)
    if match:
        return match.group(1)
    return "2026-04-20"


def _infer_impact_score(text: str) -> float:
    score = 60.0
    for keyword, bonus in DECLARATION_KEYWORDS.items():
        if keyword in text:
            score = max(score, bonus)
    if "metro" in text:
        score = max(score, 95.0)
    if "tender" in text:
        score = max(score, 92.0)
    return score


def _infer_coordinates(text: str) -> tuple[float, float]:
    lat_match = re.search(r"lat(?:itude)?\s*[:=]\s*([\d.]+)", text, re.IGNORECASE)
    lon_match = re.search(r"lon(?:gitude)?\s*[:=]\s*([\d.]+)", text, re.IGNORECASE)
    lat = first_not_none([to_float(lat_match.group(1)) if lat_match else None], fallback=28.6139)
    lon = first_not_none([to_float(lon_match.group(1)) if lon_match else None], fallback=77.2090)
    return lat, lon
