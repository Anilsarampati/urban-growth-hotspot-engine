import argparse

from urban_growth.ingestion import run_ingestion
from urban_growth.pipeline import run_pipeline


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run urban growth scoring pipeline")
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="Run web ingestion before scoring",
    )
    parser.add_argument(
        "--tune",
        action="store_true",
        help="Tune city weights using historical ROI before scoring",
    )
    args = parser.parse_args()

    if args.ingest:
        run_ingestion()

    df = run_pipeline(tune_weights=args.tune)
    print("Pipeline completed successfully.")
    print(df[["city", "zone", "growth_velocity_score", "hotspot_tier"]].to_string(index=False))
