from urban_growth.ingestion import run_ingestion


if __name__ == "__main__":
    municipal_df, market_df = run_ingestion()
    print("Ingestion completed successfully.")
    print(f"Municipal rows: {len(municipal_df)}")
    print(f"Market rows: {len(market_df)}")
