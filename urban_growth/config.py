from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "sample"
INGESTED_DIR = BASE_DIR / "data" / "ingested"
HISTORICAL_DIR = BASE_DIR / "data" / "historical"
OUTPUT_DIR = BASE_DIR / "outputs"

MUNICIPAL_FILE = DATA_DIR / "municipal_declarations.csv"
MARKET_FILE = DATA_DIR / "market_metrics.csv"
MUNICIPAL_INGESTED_FILE = INGESTED_DIR / "municipal_declarations.csv"
MARKET_INGESTED_FILE = INGESTED_DIR / "market_metrics.csv"
HISTORICAL_ROI_FILE = HISTORICAL_DIR / "historical_roi.csv"
SOURCE_CONFIG_FILE = BASE_DIR / "data" / "source_config.json"
OUTPUT_FILE = OUTPUT_DIR / "zone_growth_scores.csv"
CITY_WEIGHTS_FILE = OUTPUT_DIR / "city_weights.json"

PROJECTION_MONTHS = (24, 36, 48, 60)
