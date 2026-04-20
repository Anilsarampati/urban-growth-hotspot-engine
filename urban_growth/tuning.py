from __future__ import annotations

import itertools

import pandas as pd

from .features import min_max_norm


def _build_component_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["municipal_lead_norm"] = min_max_norm(out["municipal_lead_raw"])
    out["demand_norm"] = (
        0.30 * min_max_norm(out["listing_density"])
        + 0.30 * min_max_norm(out["rental_absorption"])
        + 0.25 * min_max_norm(out["search_volume"])
        + 0.15 * min_max_norm(out["pricing_velocity"])
    )
    out["undervaluation_norm"] = min_max_norm(out["undervaluation_raw"])
    return out


def _evaluate_weights(city_df: pd.DataFrame, weights: tuple[float, float, float]) -> float:
    municipal, demand, undervaluation = weights
    predicted = 100.0 * (
        municipal * city_df["municipal_lead_norm"]
        + demand * city_df["demand_norm"]
        + undervaluation * city_df["undervaluation_norm"]
    )
    corr = predicted.corr(city_df["observed_roi_24m"], method="pearson")
    if pd.isna(corr):
        return -1.0
    return float(corr)


def tune_city_weights(
    historical_df: pd.DataFrame,
    step: float = 0.05,
    min_rows_per_city: int = 4,
) -> dict[str, dict[str, float]]:
    if historical_df.empty:
        return {
            "default": {"municipal": 0.45, "demand": 0.35, "undervaluation": 0.20},
        }

    prepared = _build_component_frame(historical_df)
    weight_grid = []
    values = [round(v, 4) for v in _frange(0.10, 0.80, step)]
    for municipal, demand in itertools.product(values, values):
        undervaluation = round(1.0 - municipal - demand, 4)
        if undervaluation < 0.10:
            continue
        weight_grid.append((municipal, demand, undervaluation))

    result = {
        "default": {"municipal": 0.45, "demand": 0.35, "undervaluation": 0.20},
    }

    for city, city_df in prepared.groupby("city"):
        if len(city_df) < min_rows_per_city:
            continue

        best_score = -1.0
        best_weights = (0.45, 0.35, 0.20)
        for weights in weight_grid:
            score = _evaluate_weights(city_df, weights)
            if score > best_score:
                best_score = score
                best_weights = weights

        result[str(city)] = {
            "municipal": best_weights[0],
            "demand": best_weights[1],
            "undervaluation": best_weights[2],
        }

    return result


def _frange(start: float, stop: float, step: float) -> list[float]:
    values = []
    current = start
    while current <= stop + 1e-9:
        values.append(round(current, 4))
        current += step
    return values
