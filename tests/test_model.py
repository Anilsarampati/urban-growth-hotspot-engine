import pandas as pd

from urban_growth.model import add_projections, compute_growth_velocity_score


def test_growth_velocity_score_bounds() -> None:
    df = pd.DataFrame(
        {
            "city": ["NCR", "NCR", "NCR"],
            "zone": ["A", "B", "C"],
            "municipal_lead_raw": [10, 50, 100],
            "listing_density": [100, 200, 300],
            "rental_absorption": [60, 70, 80],
            "search_volume": [300, 500, 800],
            "pricing_velocity": [0.01, 0.03, 0.06],
            "undervaluation_raw": [0.0002, 0.0004, 0.0007],
        }
    )

    scored = compute_growth_velocity_score(df)

    assert (scored["growth_velocity_score"] >= 0).all()
    assert (scored["growth_velocity_score"] <= 100).all()
    assert "w_municipal" in scored.columns


def test_projection_columns_created() -> None:
    df = pd.DataFrame(
        {
            "growth_velocity_score": [10.0, 20.0],
        }
    )

    projected = add_projections(df, (24, 60))

    assert "projection_24m" in projected.columns
    assert "projection_60m" in projected.columns
