from __future__ import annotations

import numpy as np
import pandas as pd


def min_max_norm(series: pd.Series) -> pd.Series:
    min_value = series.min()
    max_value = series.max()
    if pd.isna(min_value) or pd.isna(max_value) or max_value == min_value:
        return pd.Series(np.zeros(len(series)), index=series.index, dtype=float)
    return (series - min_value) / (max_value - min_value)


def build_zone_feature_table(
    municipal_df: pd.DataFrame,
    market_df: pd.DataFrame,
) -> pd.DataFrame:
    municipal_zone = (
        municipal_df.groupby(["city", "zone"], as_index=False)
        .agg(
            {
                "infra_impact_score": "mean",
                "lat": "mean",
                "lon": "mean",
            }
        )
        .rename(columns={"infra_impact_score": "municipal_lead_raw"})
    )

    municipal_city = (
        municipal_df.groupby("city", as_index=False)
        .agg(
            {
                "infra_impact_score": "mean",
                "lat": "mean",
                "lon": "mean",
            }
        )
        .rename(
            columns={
                "infra_impact_score": "city_municipal_lead_raw",
                "lat": "city_lat",
                "lon": "city_lon",
            }
        )
    )

    market = market_df.copy()
    market["pricing_velocity"] = (
        (market["price_psf_current"] - market["price_psf_12m_ago"])
        / market["price_psf_12m_ago"].replace(0, np.nan)
    )
    market["pricing_velocity"] = market["pricing_velocity"].fillna(0.0)

    market["undervaluation_raw"] = (
        market["rental_yield"] / market["price_psf_current"].replace(0, np.nan)
    )
    market["undervaluation_raw"] = market["undervaluation_raw"].fillna(0.0)

    merged = market.merge(municipal_city, on="city", how="left")
    merged = merged.merge(municipal_zone, on=["city", "zone"], how="left")

    merged["municipal_lead_raw"] = merged["municipal_lead_raw"].combine_first(
        merged["city_municipal_lead_raw"]
    )
    merged["lat"] = merged["lat"].combine_first(merged["city_lat"])
    merged["lon"] = merged["lon"].combine_first(merged["city_lon"])
    merged = merged.drop(columns=["city_municipal_lead_raw", "city_lat", "city_lon"])

    merged = merged.dropna(subset=["municipal_lead_raw", "lat", "lon"])
    return merged
