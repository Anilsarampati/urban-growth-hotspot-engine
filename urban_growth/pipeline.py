from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import (
    CITY_WEIGHTS_FILE,
    HISTORICAL_ROI_FILE,
    MARKET_FILE,
    MARKET_INGESTED_FILE,
    MUNICIPAL_FILE,
    MUNICIPAL_INGESTED_FILE,
    OUTPUT_DIR,
    OUTPUT_FILE,
    PROJECTION_MONTHS,
)
from .features import build_zone_feature_table
from .io import (
    load_city_weights,
    load_historical_roi_data,
    load_market_data,
    load_municipal_data,
    save_city_weights,
)
from .model import add_projections, compute_growth_velocity_score
from .tuning import tune_city_weights


def _resolve_input_files() -> tuple[Path, Path]:
    municipal_path = MUNICIPAL_INGESTED_FILE if MUNICIPAL_INGESTED_FILE.exists() else MUNICIPAL_FILE
    market_path = MARKET_INGESTED_FILE if MARKET_INGESTED_FILE.exists() else MARKET_FILE
    return municipal_path, market_path


def run_pipeline(tune_weights: bool = False) -> pd.DataFrame:
    municipal_path, market_path = _resolve_input_files()
    municipal_df = load_municipal_data(municipal_path)
    market_df = load_market_data(market_path)

    feature_df = build_zone_feature_table(municipal_df, market_df)

    city_weights = load_city_weights(CITY_WEIGHTS_FILE)
    if tune_weights and HISTORICAL_ROI_FILE.exists():
        historical_df = load_historical_roi_data(HISTORICAL_ROI_FILE)
        city_weights = tune_city_weights(historical_df)
        save_city_weights(city_weights, CITY_WEIGHTS_FILE)

    scored_df = compute_growth_velocity_score(feature_df, city_weights=city_weights)
    projected_df = add_projections(scored_df, PROJECTION_MONTHS)

    ordered_cols = [
        "city",
        "zone",
        "lat",
        "lon",
        "municipal_lead_raw",
        "listing_density",
        "rental_absorption",
        "search_volume",
        "pricing_velocity",
        "undervaluation_raw",
        "w_municipal",
        "w_demand",
        "w_undervaluation",
        "growth_velocity_score",
        "hotspot_tier",
        "projection_24m",
        "projection_36m",
        "projection_48m",
        "projection_60m",
    ]
    result = projected_df[ordered_cols].sort_values(
        ["city", "growth_velocity_score"], ascending=[True, False]
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_FILE, index=False)

    return result
