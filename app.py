from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

from urban_growth.config import OUTPUT_FILE
from urban_growth.pipeline import run_pipeline

st.set_page_config(page_title="Urban Growth Hotspot Engine", page_icon="U", layout="wide")

st.title("Predictive Urban Growth Hotspot Dashboard")
st.caption("24-60 month growth projection using municipal intent and market demand signals")

if not Path(OUTPUT_FILE).exists():
    st.info("No output file found. Running pipeline with sample data...")
    run_pipeline()

scores = pd.read_csv(OUTPUT_FILE)

left, right = st.columns([2, 1])
with left:
    st.subheader("Zone Heat Map")

    scores["radius"] = scores["growth_velocity_score"] * 65
    scores["color_r"] = (255 * (scores["growth_velocity_score"] / 100)).astype(int)
    scores["color_g"] = (180 * (1 - (scores["growth_velocity_score"] / 100))).astype(int)
    scores["color_b"] = 70

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=scores,
        get_position="[lon, lat]",
        get_radius="radius",
        get_fill_color="[color_r, color_g, color_b, 160]",
        pickable=True,
        auto_highlight=True,
    )

    view = pdk.ViewState(
        latitude=float(scores["lat"].mean()),
        longitude=float(scores["lon"].mean()),
        zoom=9,
        pitch=40,
    )

    tooltip = {
        "html": "<b>{zone}</b><br/>Score: {growth_velocity_score}<br/>Tier: {hotspot_tier}",
        "style": {"backgroundColor": "#1f2937", "color": "white"},
    }

    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view, tooltip=tooltip))

with right:
    st.subheader("Top Hotspots")
    top = scores.sort_values("growth_velocity_score", ascending=False).head(5)
    st.dataframe(
        top[["city", "zone", "growth_velocity_score", "hotspot_tier"]],
        use_container_width=True,
    )

st.subheader("Detailed Projection Table")
st.dataframe(
    scores.sort_values("growth_velocity_score", ascending=False),
    use_container_width=True,
)
