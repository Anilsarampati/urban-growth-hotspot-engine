from __future__ import annotations

from datetime import date

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .common import build_session, clean_text, first_not_none, to_float


def scrape_municipal_portals(urls: list[str], default_city: str = "default") -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    session = build_session()

    for url in urls:
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException:
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        for table in soup.find_all("table"):
            headers = [clean_text(th.get_text(" ", strip=True)).lower() for th in table.find_all("th")]
            for tr in table.find_all("tr"):
                cells = [clean_text(td.get_text(" ", strip=True)) for td in tr.find_all("td")]
                if len(cells) < 2:
                    continue

                record = _parse_municipal_row(headers, cells)
                if record is None:
                    continue
                record["city"] = record.get("city") or default_city
                record["source_url"] = url
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


def _parse_municipal_row(headers: list[str], cells: list[str]) -> dict[str, object] | None:
    combined = " ".join(cells).lower()
    if "zone" not in combined and "sector" not in combined and "ward" not in combined:
        return None

    zone = _find_by_keywords(headers, cells, ["zone", "sector", "ward"]) or cells[0]
    declaration_type = _find_by_keywords(headers, cells, ["project", "work", "declaration", "type"]) or "Public Works"
    date_text = _find_by_keywords(headers, cells, ["date", "announced", "published"]) or str(date.today())

    infra_score = first_not_none(
        [
            to_float(_find_by_keywords(headers, cells, ["impact", "priority", "score"]) or ""),
            to_float(cells[-1]),
        ],
        fallback=60.0,
    )

    lat = first_not_none(
        [
            to_float(_find_by_keywords(headers, cells, ["lat"] ) or ""),
        ],
        fallback=28.61,
    )
    lon = first_not_none(
        [
            to_float(_find_by_keywords(headers, cells, ["lon", "lng", "long"]) or ""),
        ],
        fallback=77.20,
    )

    city = _find_by_keywords(headers, cells, ["city", "district"])

    return {
        "city": city,
        "zone": zone,
        "lat": lat,
        "lon": lon,
        "declaration_type": declaration_type,
        "announced_date": date_text,
        "infra_impact_score": float(infra_score),
    }


def _find_by_keywords(headers: list[str], cells: list[str], keywords: list[str]) -> str | None:
    for index, header in enumerate(headers):
        if any(keyword in header for keyword in keywords) and index < len(cells):
            return cells[index]
    return None
