from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

MUNICIPAL_REQUIRED = {
    "zone",
    "lat",
    "lon",
    "declaration_type",
    "announced_date",
    "infra_impact_score",
}

MARKET_REQUIRED = {
    "zone",
    "listing_density",
    "price_psf_current",
    "price_psf_12m_ago",
    "rental_yield",
    "rental_absorption",
    "search_volume",
}

HISTORICAL_REQUIRED = {
    "city",
    "zone",
    "municipal_lead_raw",
    "listing_density",
    "rental_absorption",
    "search_volume",
    "pricing_velocity",
    "undervaluation_raw",
    "observed_roi_24m",
}


def _validate_columns(df: pd.DataFrame, required: set[str], file_name: str) -> None:
    missing = required.difference(df.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"Missing required columns in {file_name}: {missing_text}")


def _ensure_city_column(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "city" not in out.columns:
        out["city"] = "default"
    out["city"] = out["city"].fillna("default").astype(str)
    return out


def load_municipal_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    _validate_columns(df, MUNICIPAL_REQUIRED, path.name)
    df = _ensure_city_column(df)
    df["announced_date"] = pd.to_datetime(df["announced_date"], errors="coerce", dayfirst=True)
    df["infra_impact_score"] = pd.to_numeric(df["infra_impact_score"], errors="coerce")
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    return df.dropna(subset=["zone", "city", "lat", "lon", "infra_impact_score"])


def load_market_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    _validate_columns(df, MARKET_REQUIRED, path.name)
    df = _ensure_city_column(df)
    numeric_cols = [
        "listing_density",
        "price_psf_current",
        "price_psf_12m_ago",
        "rental_yield",
        "rental_absorption",
        "search_volume",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["zone", "city", *numeric_cols])


def load_historical_roi_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    _validate_columns(df, HISTORICAL_REQUIRED, path.name)
    df = _ensure_city_column(df)

    numeric_cols = [
        "municipal_lead_raw",
        "listing_density",
        "rental_absorption",
        "search_volume",
        "pricing_velocity",
        "undervaluation_raw",
        "observed_roi_24m",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.dropna(subset=["city", "zone", *numeric_cols])


def save_city_weights(weights: dict[str, dict[str, float]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(weights, f, indent=2)


def load_city_weights(path: Path) -> dict[str, dict[str, float]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return {}

    safe: dict[str, dict[str, float]] = {}
    for city, values in data.items():
        if not isinstance(city, str) or not isinstance(values, dict):
            continue
        municipal = float(values.get("municipal", 0.45))
        demand = float(values.get("demand", 0.35))
        undervaluation = float(values.get("undervaluation", 0.20))
        total = municipal + demand + undervaluation
        if total <= 0:
            continue
        safe[city] = {
            "municipal": municipal / total,
            "demand": demand / total,
            "undervaluation": undervaluation / total,
        }
    return safe
