from __future__ import annotations

import pandas as pd

from .features import min_max_norm


DEFAULT_WEIGHTS = {
    "municipal": 0.45,
    "demand": 0.35,
    "undervaluation": 0.20,
}


def _resolve_city_weight(city: str, city_weights: dict[str, dict[str, float]]) -> dict[str, float]:
    if city in city_weights:
        return city_weights[city]
    return city_weights.get("default", DEFAULT_WEIGHTS)


def compute_growth_velocity_score(
    feature_df: pd.DataFrame,
    city_weights: dict[str, dict[str, float]] | None = None,
) -> pd.DataFrame:
    df = feature_df.copy()
    weights_map = city_weights or {}

    demand_raw = (
        0.30 * min_max_norm(df["listing_density"])
        + 0.30 * min_max_norm(df["rental_absorption"])
        + 0.25 * min_max_norm(df["search_volume"])
        + 0.15 * min_max_norm(df["pricing_velocity"])
    )

    municipal_lead_norm = min_max_norm(df["municipal_lead_raw"])
    undervaluation_norm = min_max_norm(df["undervaluation_raw"])

    if "city" not in df.columns:
        df["city"] = "default"

    municipal_weight = pd.to_numeric(
        df["city"].astype(str).map(
        lambda city: _resolve_city_weight(city, weights_map)["municipal"]
        ),
        errors="coerce",
    ).fillna(DEFAULT_WEIGHTS["municipal"])
    demand_weight = pd.to_numeric(
        df["city"].astype(str).map(
        lambda city: _resolve_city_weight(city, weights_map)["demand"]
        ),
        errors="coerce",
    ).fillna(DEFAULT_WEIGHTS["demand"])
    undervaluation_weight = pd.to_numeric(
        df["city"].astype(str).map(
        lambda city: _resolve_city_weight(city, weights_map)["undervaluation"]
        ),
        errors="coerce",
    ).fillna(DEFAULT_WEIGHTS["undervaluation"])

    growth_velocity_score = 100.0 * (
        municipal_weight * municipal_lead_norm
        + demand_weight * demand_raw
        + undervaluation_weight * undervaluation_norm
    )

    df["municipal_lead_norm"] = municipal_lead_norm
    df["demand_norm"] = demand_raw
    df["undervaluation_norm"] = undervaluation_norm
    df["w_municipal"] = municipal_weight
    df["w_demand"] = demand_weight
    df["w_undervaluation"] = undervaluation_weight
    df["growth_velocity_score"] = growth_velocity_score.round(2)

    df["hotspot_tier"] = pd.cut(
        df["growth_velocity_score"],
        bins=[-1, 33, 66, 100],
        labels=["Monitor", "Emerging", "High-Growth"],
    )

    return df


def add_projections(df: pd.DataFrame, horizons: tuple[int, ...]) -> pd.DataFrame:
    out = df.copy()
    for months in horizons:
        horizon_factor = 1.0 + (months / 60.0) * 0.40
        out[f"projection_{months}m"] = (out["growth_velocity_score"] * horizon_factor).round(2)
    return out
