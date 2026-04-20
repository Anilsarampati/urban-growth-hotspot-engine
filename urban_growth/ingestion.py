from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .config import (
    MARKET_INGESTED_FILE,
    MUNICIPAL_INGESTED_FILE,
    SOURCE_CONFIG_FILE,
)
from .scrapers.ninetynineacres import scrape_99acres_portals
from .scrapers.magicbricks import scrape_magicbricks_portals
from .scrapers.municipal_pdf import scrape_municipal_pdf_portals
from .scrapers.listing import scrape_listing_portals
from .scrapers.municipal import scrape_municipal_portals


def run_ingestion(config_path: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    source_config = _load_config(config_path or SOURCE_CONFIG_FILE)

    municipal_urls = source_config.get("municipal_urls", [])
    municipal_pdf_urls = source_config.get("municipal_pdf_urls", [])
    listing_urls = source_config.get("listing_urls", [])
    magicbricks_urls = source_config.get("magicbricks_urls", [])
    ninetynineacres_urls = source_config.get("99acres_urls", [])
    default_city = str(source_config.get("default_city", "default"))

    municipal_frames = [
        scrape_municipal_portals(municipal_urls, default_city=default_city),
        scrape_municipal_pdf_portals(municipal_pdf_urls, default_city=default_city),
    ]
    listing_frames = [
        scrape_listing_portals(listing_urls, default_city=default_city),
        scrape_magicbricks_portals(magicbricks_urls, default_city=default_city),
        scrape_99acres_portals(ninetynineacres_urls, default_city=default_city),
    ]

    municipal_df = pd.concat(municipal_frames, ignore_index=True, sort=False)
    market_df = pd.concat(listing_frames, ignore_index=True, sort=False)

    if municipal_df.empty:
        raise RuntimeError("Municipal scraper returned no rows. Update municipal_urls in source_config.json")
    if market_df.empty:
        raise RuntimeError("Listing scraper returned no rows. Update listing_urls in source_config.json")

    MUNICIPAL_INGESTED_FILE.parent.mkdir(parents=True, exist_ok=True)
    municipal_df.to_csv(MUNICIPAL_INGESTED_FILE, index=False)
    market_df.to_csv(MARKET_INGESTED_FILE, index=False)

    return municipal_df, market_df


def _load_config(path: Path) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing source configuration: {path}. Create from data/source_config.example.json"
        )
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("source_config.json must contain a JSON object")
    return data
