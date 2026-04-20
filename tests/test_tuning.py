import pandas as pd

from urban_growth.tuning import tune_city_weights


def test_tune_city_weights_returns_city_entries() -> None:
    historical = pd.DataFrame(
        {
            "city": ["NCR", "NCR", "NCR", "NCR", "Pune", "Pune", "Pune", "Pune"],
            "zone": ["A", "B", "C", "D", "P1", "P2", "P3", "P4"],
            "municipal_lead_raw": [70, 60, 85, 65, 80, 62, 88, 74],
            "listing_density": [600, 520, 750, 690, 640, 510, 760, 680],
            "rental_absorption": [72, 67, 79, 71, 74, 69, 80, 73],
            "search_volume": [700, 590, 820, 690, 710, 600, 840, 730],
            "pricing_velocity": [0.10, 0.07, 0.14, 0.09, 0.11, 0.08, 0.15, 0.10],
            "undervaluation_raw": [0.00041, 0.00052, 0.00039, 0.00044, 0.00042, 0.00055, 0.00038, 0.00043],
            "observed_roi_24m": [15.5, 12.2, 19.4, 14.1, 16.3, 12.6, 20.1, 15.0],
        }
    )

    weights = tune_city_weights(historical)

    assert "default" in weights
    assert "NCR" in weights
    assert "Pune" in weights

    for city in ["NCR", "Pune"]:
        total = (
            weights[city]["municipal"]
            + weights[city]["demand"]
            + weights[city]["undervaluation"]
        )
        assert abs(total - 1.0) < 1e-9
