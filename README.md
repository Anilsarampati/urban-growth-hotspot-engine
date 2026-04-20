# Predictive Urban Growth Modeling for Real Estate Investment

This project builds a predictive geospatial analytics engine for identifying high-growth urban zones over a 24 to 60 month horizon.

It now includes all three advanced requirements:

- Real web scrapers for municipal and listing portals, feeding the same scoring pipeline.
- City-specific model weight tuning from historical ROI outcomes.
- Monthly scheduled ingestion + retraining + rescoring automation.

## End-to-End Workflow

1. Ingestion layer

- Municipal PDF scraper parses public notices, policies, and declarations.
- Municipal HTML scraper parses public portal tables for projects, declarations, and infra indicators.
- MagicBricks and 99acres adapters parse source-specific listing pages for listing density, pricing, rental, and demand signals.
- Ingested outputs are saved to data/ingested.

2. Feature engineering

- Municipal lead indicator from infra impact declarations.
- Demand indicator from listing density, rental absorption, search volume, and pricing velocity.
- Undervaluation signal from rental yield relative to price.

3. City-specific ROI tuning

- Historical ROI dataset (data/historical/historical_roi.csv) is used to optimize municipal, demand, and undervaluation weights for each city.
- Best city-wise weights are saved to outputs/city_weights.json.

4. Scoring and projection

- Growth Velocity Score is calculated zone-wise with city-specific top-level weights.
- Projection columns are generated for 24m, 36m, 48m, and 60m horizons.

5. Visualization

- Streamlit + PyDeck geospatial dashboard reads outputs/zone_growth_scores.csv.

6. Monthly automation

- APScheduler cron job runs monthly ingestion + retraining + scoring refresh.

## Model Formula

For each city, the score is:

GVS = 100 _ (
W_municipal(city) _ MunicipalLeadNorm

- W_demand(city) \* DemandNorm
- W_undervaluation(city) \* UndervaluationNorm
  )

Subject to:

W_municipal + W_demand + W_undervaluation = 1

Default weights are used when tuned city weights are unavailable.

## Project Structure

- run_pipeline.py: Pipeline runner with optional ingestion and tuning flags
- run_ingestion.py: Manual scraper ingestion entrypoint
- monthly_refresh.py: Monthly scheduler for ingestion + retrain + scoring
- app.py: Streamlit heat-map dashboard
- urban_growth/config.py: Paths and constants
- urban_growth/io.py: CSV validation and weight persistence helpers
- urban_growth/features.py: Feature engineering logic
- urban_growth/model.py: Scoring logic with city-specific weights
- urban_growth/tuning.py: Historical ROI weight optimization
- urban_growth/ingestion.py: Config-driven scraper orchestration
- urban_growth/scrapers/: Municipal PDF, MagicBricks, and 99acres scrapers
- data/sample/: Baseline sample datasets
- data/ingested/: Scraped latest datasets
- data/historical/: ROI history for tuning
- data/source_config.example.json: Source URL configuration template
- data/source_config.json: Ready-to-run default source configuration
- outputs/: Scoring outputs and tuned city weights
- tests/: Unit tests

## Setup

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Configure Scraper Sources

1. The repository already includes a ready-to-run config at data/source_config.json.
2. data/source_config.example.json contains the same live URL set if you want a template copy.
3. Replace URLs only if you want to target different cities or sources.

## Run Commands

1. Ingestion only

```powershell
python run_ingestion.py
```

2. Pipeline on latest data (uses ingested files if available, else sample)

```powershell
python run_pipeline.py
```

If you want the project to ingest the configured live sources before scoring, use:

```powershell
python run_pipeline.py --ingest
```

3. Pipeline with ROI tuning

```powershell
python run_pipeline.py --tune
```

4. Ingest + tune + score in one command

```powershell
python run_pipeline.py --ingest --tune
```

5. Monthly scheduled refresh

```powershell
python monthly_refresh.py
```

6. Run a one-time refresh job immediately

```powershell
python monthly_refresh.py --run-once
```

7. Launch dashboard

```powershell
streamlit run app.py
```

## Output Artifacts

- outputs/zone_growth_scores.csv
- outputs/city_weights.json

## Testing

```powershell
python -m pytest -q
```

## Deploy To Public Link

Fastest path:

1. Push this folder to a GitHub repository.
2. Deploy the repo on Streamlit Community Cloud using `app.py` as the entrypoint.
3. The service will generate a public URL that you can share.

Alternative:

1. Use Render with the included `render.yaml` and `Dockerfile`.
2. Render will also generate a public URL after deployment.
