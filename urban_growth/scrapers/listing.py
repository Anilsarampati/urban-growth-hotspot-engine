from __future__ import annotations

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .common import build_session, clean_text, first_not_none, to_float


def scrape_listing_portals(urls: list[str], default_city: str = "default") -> pd.DataFrame:
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
                if len(cells) < 3:
                    continue

                record = _parse_listing_row(headers, cells)
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
                "listing_density",
                "price_psf_current",
                "price_psf_12m_ago",
                "rental_yield",
                "rental_absorption",
                "search_volume",
            ]
        )

    return pd.DataFrame(rows)


def _parse_listing_row(headers: list[str], cells: list[str]) -> dict[str, object] | None:
    zone = _find_by_keywords(headers, cells, ["zone", "locality", "sector", "ward"]) or cells[0]
    if not zone:
        return None

    listing_density = first_not_none(
        [to_float(_find_by_keywords(headers, cells, ["listing", "inventory"]) or "")],
        fallback=0.0,
    )
    price_current = first_not_none(
        [to_float(_find_by_keywords(headers, cells, ["current", "price", "psf"]) or "")],
        fallback=0.0,
    )
    price_12m_ago = first_not_none(
        [to_float(_find_by_keywords(headers, cells, ["12m", "last year", "previous"]) or "")],
        fallback=price_current,
    )
    rental_yield = first_not_none(
        [to_float(_find_by_keywords(headers, cells, ["yield", "rental"]) or "")],
        fallback=0.0,
    )
    rental_absorption = first_not_none(
        [to_float(_find_by_keywords(headers, cells, ["absorption", "occupancy"]) or "")],
        fallback=0.0,
    )
    search_volume = first_not_none(
        [to_float(_find_by_keywords(headers, cells, ["search", "demand"]) or "")],
        fallback=0.0,
    )

    city = _find_by_keywords(headers, cells, ["city", "district"])

    return {
        "city": city,
        "zone": zone,
        "listing_density": float(listing_density),
        "price_psf_current": float(price_current),
        "price_psf_12m_ago": float(price_12m_ago),
        "rental_yield": float(rental_yield),
        "rental_absorption": float(rental_absorption),
        "search_volume": float(search_volume),
    }


def _find_by_keywords(headers: list[str], cells: list[str], keywords: list[str]) -> str | None:
    for index, header in enumerate(headers):
        if any(keyword in header for keyword in keywords) and index < len(cells):
            return cells[index]
    return None
