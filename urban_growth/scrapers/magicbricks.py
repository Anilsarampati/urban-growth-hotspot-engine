from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .common import build_session, clean_text, first_not_none, to_float


@dataclass
class MagicBricksPageSummary:
    listing_density: float
    search_volume: float


def scrape_magicbricks_portals(urls: list[str], default_city: str = "default") -> pd.DataFrame:
    session = build_session()
    rows: list[dict[str, object]] = []

    for url in urls:
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException:
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        page_summary = _summarize_page(soup)

        for card in _extract_cards(soup):
            record = _parse_magicbricks_card(card, url, default_city, page_summary)
            if record is not None:
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


def _extract_cards(soup: BeautifulSoup) -> list[BeautifulSoup]:
    anchors = soup.find_all("a", href=lambda href: bool(href) and ("pdpid" in href or "project" in href))
    cards: list[BeautifulSoup] = []
    seen: set[str] = set()

    for anchor in anchors:
        container = anchor.find_parent(["article", "li", "div", "section"]) or anchor.parent
        if container is None:
            continue
        marker = clean_text(container.get_text(" ", strip=True))[:300]
        if not marker or marker in seen:
            continue
        seen.add(marker)
        cards.append(container)

    return cards


def _summarize_page(soup: BeautifulSoup) -> MagicBricksPageSummary:
    text = clean_text(soup.get_text(" ", strip=True))
    listing_density = 0.0
    search_volume = 0.0

    density_match = re.search(r"Properties\s*\((\d[\d,]*)\)", text)
    if density_match:
        listing_density = float(density_match.group(1).replace(",", ""))
        search_volume = listing_density
    else:
        title_match = re.search(r"(\d[\d,]*)\+?\s*results?", text, re.IGNORECASE)
        if title_match:
            listing_density = float(title_match.group(1).replace(",", ""))
            search_volume = listing_density

    return MagicBricksPageSummary(listing_density=listing_density, search_volume=search_volume)


def _parse_magicbricks_card(
    card: BeautifulSoup,
    source_url: str,
    default_city: str,
    page_summary: MagicBricksPageSummary,
) -> dict[str, object] | None:
    text = clean_text(card.get_text(" ", strip=True))
    if not text:
        return None

    title = _find_title(card) or _find_pattern(text, r"^(.*?)\s+(?:SUPER AREA|CARPET AREA|STATUS|TRANSACTION|FURNISHING)")
    locality = _find_pattern(text, r"for sale in ([^\.]+?)(?:\. |$)")
    city = _infer_city(text, default_city)
    price_psf_current = _find_price_per_sqft(text)
    price_current = _find_price(text)
    area = _find_area(text)
    transaction = _find_pattern(text, r"TRANSACTION\s+([A-Za-z ]+?)(?:\s{2,}|$)") or "New Property"
    status = _find_status(text)

    effective_area = area or _estimate_area_from_context(text, title)
    if price_psf_current <= 0.0 and price_current > 0.0 and effective_area > 0.0:
        price_psf_current = price_current / effective_area

    if title is None and locality is None:
        return None

    price_12m_ago = price_psf_current * 0.92 if price_psf_current > 0 else 0.0
    rental_yield = _estimate_rental_yield(price_current, effective_area or area)
    rental_absorption = 85.0 if "ready to move" in text.lower() else 68.0
    search_volume = page_summary.search_volume or page_summary.listing_density
    listing_density = page_summary.listing_density or 1.0

    zone = locality or title or "Unknown"
    declaration_type = f"MagicBricks {transaction}"

    return {
        "city": city,
        "zone": zone,
        "listing_density": float(listing_density),
        "price_psf_current": float(price_psf_current or 0.0),
        "price_psf_12m_ago": float(price_12m_ago),
        "rental_yield": float(rental_yield),
        "rental_absorption": float(rental_absorption),
        "search_volume": float(search_volume),
        "property_title": title or zone,
        "property_status": status or "Unknown",
        "transaction_type": transaction,
        "area_sqft": float(effective_area or area or 0.0),
        "price_current": float(price_current or 0.0),
        "declaration_type": declaration_type,
        "source_url": source_url,
    }


def _find_title(card: BeautifulSoup) -> str | None:
    for heading in card.find_all(["h1", "h2", "h3", "h4"]):
        text = clean_text(heading.get_text(" ", strip=True))
        if text:
            return text
    for anchor in card.find_all("a"):
        text = clean_text(anchor.get_text(" ", strip=True))
        if text and len(text) > 8:
            return text
    return None


def _find_price(text: str) -> float:
    matches = re.findall(r"₹\s*([\d.,]+)\s*(Cr|Lac)?", text)
    if not matches:
        return 0.0
    amount, unit = matches[0]
    value = float(amount.replace(",", ""))
    if unit == "Cr":
        return value * 10_000_000
    if unit == "Lac":
        return value * 100_000
    return value


def _find_price_per_sqft(text: str) -> float:
    match = re.search(r"₹\s*([\d,]+)\s*per sqft", text, re.IGNORECASE)
    return float(match.group(1).replace(",", "")) if match else 0.0


def _find_area(text: str) -> float:
    patterns = [
        r"(?:SUPER AREA|CARPET AREA|BUILT UP AREA)\s+([\d,]+(?:\.\d+)?)\s*(sqft|sqyrd)",
        r"Covered area is\s+([\d,]+(?:\.\d+)?)\s*Sq-ft",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = float(match.group(1).replace(",", ""))
            unit = match.group(2).lower() if len(match.groups()) > 1 else "sqft"
            return value * 9.0 if unit == "sqyrd" else value
    return 0.0


def _estimate_rental_yield(price_current: float, area_sqft: float) -> float:
    if price_current <= 0 or area_sqft <= 0:
        return 0.0
    approximate_monthly_rent = max(25_000.0, area_sqft * 35.0)
    annual_rent = approximate_monthly_rent * 12.0
    return round((annual_rent / price_current) * 100.0, 2)


def _estimate_area_from_context(text: str, title: str | None) -> float:
    combined = f"{title or ''} {text}".lower()
    if any(keyword in combined for keyword in ["shop", "showroom"]):
        return 1200.0
    if any(keyword in combined for keyword in ["builder floor", "independent house"]):
        return 1800.0
    if "apartment" in combined or "flat" in combined:
        return 1500.0
    return 1000.0


def _infer_city(text: str, default_city: str) -> str:
    lowered = text.lower()
    if "pune" in lowered:
        return "Pune"
    if "mumbai" in lowered:
        return "Mumbai"
    if "bangalore" in lowered or "bengaluru" in lowered:
        return "Bangalore"
    if "gurgaon" in lowered or "gurugram" in lowered:
        return "Gurgaon"
    if "noida" in lowered:
        return "Noida"
    return default_city


def _find_status(text: str) -> str | None:
    status_match = re.search(r"\b(Ready to Move|Under Construction|New Property|Resale)\b", text, re.IGNORECASE)
    return status_match.group(1) if status_match else None


def _find_pattern(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None
    return clean_text(match.group(1))
