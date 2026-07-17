# NYC Taxi Data Pipeline - Bruin Automated

This is an end-to-end data pipeline built with **Bruin** that ingests, transforms, and reports on NYC taxi trip data. The pipeline orchestrates the full flow from data ingestion through staging to final reporting using DuckDB as the local data warehouse.

## Project Structure

```
zoomcampAutomated/
├── .bruin.yml                          # Bruin environment configuration
├── pipeline/
│   ├── pipeline.yml                    # Pipeline definition with schedule and variables
│   └── assets/
│       ├── ingestion/
│       │   ├── trips.py                # Python asset to fetch and load trip data
│       │   ├── requirements.txt        # Python dependencies for ingestion asset
│       │   ├── payment_lookup.asset.yml # Seed asset for payment type lookup
│       │   └── payment_lookup.csv      # Static lookup data
│       ├── staging/
│       │   └── trips.sql               # SQL asset for data cleaning and deduplication
│       └── reports/
│           └── trips_report.sql        # SQL asset for aggregated trip reporting
```

## Setup Instructions

### 1. Configure Bruin Environment

The `.bruin.yml` file defines the environment and DuckDB connection:

```yaml
environments:
  default:
    connections:
      duckdb-default:
        type: duckdb
        path: /tmp/bruin_duckdb.db
```

This creates a local DuckDB database at `/tmp/bruin_duckdb.db` for development.

### 2. Pipeline Configuration

The `pipeline/pipeline.yml` file defines:

- **name**: `nyc_taxi` - The pipeline name
- **schedule**: `monthly` - Runs monthly (can be changed to daily, weekly, etc.)
- **start_date**: `2022-01-01` - The earliest date for backfills
- **default_connections**: Maps `duckdb` to `duckdb-default`
- **variables**: Defines `taxi_types` with a default of `["yellow"]`

### 3. Assets

#### Ingestion Layer (`assets/ingestion/`)

**trips.py** - Python asset that:
- Fetches NYC taxi parquet files from the TLC public bucket
- Uses the `--var taxi_types` parameter to specify which taxi types to ingest (e.g., `["green", "yellow"]`)
- Uses the date range from `--start-date` and `--end-date` to fetch specific months
- Loads data into `ingestion.trips` table in DuckDB

Dependencies: `pandas`, `pyarrow`, `python-dateutil`

**payment_lookup.asset.yml + payment_lookup.csv** - Seed asset that:
- Loads a static CSV file with payment type lookup values
- Creates the `ingestion.payment_lookup` table with columns: `payment_type_id`, `payment_type_name`
- Includes data quality checks (not_null, unique)

#### Staging Layer (`assets/staging/`)

**trips.sql** - SQL asset that:
- Cleans and deduplicates raw trip data from `ingestion.trips`
- Uses a window function to identify and remove duplicates
- Joins with payment lookup table to enrich payment type information
- Creates the `staging.trips` table with deduplicated, enriched data
- Runs custom quality check to ensure row count is positive
- Materialization: `time_interval` strategy with `pickup_datetime` as incremental key

#### Reporting Layer (`assets/reports/`)

**trips_report.sql** - SQL asset that:
- Aggregates staged trip data by trip date, service type, and payment type
- Computes trip count and total amount per aggregation bucket
- Creates the `reports.trips_report` table
- Includes data quality checks (non_negative for trip_count and total_amount)
- Materialization: `time_interval` strategy with `trip_date` as incremental key

## Running the Pipeline

### Basic Run (with defaults)

```bash
cd pipeline
bruin run .
```

This uses:
- Default start date from `pipeline.yml`: `2022-01-01`
- Default taxi types: `["yellow"]`

### Custom Date Range

```bash
cd pipeline
bruin run --start-date 2024-01-01 --end-date 2024-01-02 .
```

### Custom Taxi Types

```bash
cd pipeline
bruin run --var 'taxi_types=["green","yellow"]' .
```

### Full Example with Both Customizations

```bash
cd pipeline
bruin run --start-date 2024-01-01 --end-date 2024-01-02 --var 'taxi_types=["green","yellow"]' .
```

## Validation

To validate the pipeline without running it:

```bash
cd pipeline
bruin validate .
```

This checks all asset configurations and dependencies for errors.

## Data Flow

```
NYC TLC Public Bucket (Parquet Files)
        ↓
    trips.py (ingestion)
        ↓
ingestion.trips (raw data)
        ↓
    trips.sql (staging)
        ↓
staging.trips (clean data)
        ↓
trips_report.sql (reporting)
        ↓
reports.trips_report (aggregated data)
```

## Key Features

- **Incremental Processing**: Both staging and reporting use time-interval materialization strategies to efficiently process only changed data
- **Data Quality**: Built-in checks for not_null, unique constraints, and custom row count validation
- **Parameterization**: Use pipeline variables to control taxi types and date ranges without code changes
- **Dependency Management**: Assets automatically resolve dependencies (trips_report depends on staging.trips, staging.trips depends on ingestion.trips)
- **Local Development**: DuckDB provides a lightweight, embeddable SQL database perfect for development

## Notes

- The pipeline runs successfully with dates from 2022-01-01 onwards (when NYC TLC data is available)
- Each run creates/updates three main tables: `ingestion.trips`, `staging.trips`, and `reports.trips_report`
- The DuckDB database is stored locally at `/tmp/bruin_duckdb.db`
- Quality checks are automatically run after each asset to validate data integrity
