# 📌 Module 4 — Analytics Engineering with dbt and BigQuery

## Overview

This module covers the analytics engineering layer of the data pipeline using **dbt (data build tool)** to transform the raw NYC Taxi datasets loaded in previous modules into clean, organized tables ready for analysis.

The project uses:

* dbt
* BigQuery
* GitHub Codespaces
* dbt Power User extension
* (Optional) dbt Cloud

The project follows the standard dbt project structure, separating models into staging, intermediate and marts layers.

---

# 📂 Project Structure

```text
04-analytics-engineering/
├── analyses/           # Data quality reports and ad-hoc SQL
├── macros/             # Reusable Jinja functions
├── models/
│   ├── staging/        # Minimal transformations of raw data
│   ├── intermediate/   # Business logic and transformations
│   └── marts/          # Final analytical models
├── seeds/              # Static CSV lookup tables
├── snapshots/          # Slowly changing dimensions
├── tests/              # Singular SQL tests
└── dbt_project.yml     # Project configuration
```

### Folder Descriptions

| Folder    | Purpose                                                                      |
| --------- | ---------------------------------------------------------------------------- |
| analyses  | Exploratory SQL and data quality reports that are not materialized as models |
| macros    | Reusable Jinja functions shared across models                                |
| seeds     | Small CSV reference datasets loaded into BigQuery                            |
| snapshots | Track historical changes in mutable tables                                   |
| tests     | Custom SQL assertions for data quality                                       |

---

## Model Layers

| Layer        | Materialization | Purpose                                                   |
| ------------ | --------------- | --------------------------------------------------------- |
| staging      | View            | Minimal cleaning, renaming columns and casting data types |
| intermediate | Table           | Complex transformations and business logic                |
| marts        | Table           | Final analytical models for dashboards and reporting      |

---

# ⚙️ Project Setup

## 1. dbt Cloud

Configured a dbt Cloud project by:

* Connecting the GitHub repository
* Setting the project subdirectory to `04-analytics-engineering`
* Configuring the BigQuery connection

> **Note:** The Problems panel may display a false `IoError` for `dbt_project.yml`. This is a known Fusion IDE issue and can be ignored if `dbt debug` succeeds.

---

## 2. GitHub Codespaces

Created a local dbt profile outside the repository:

```bash
mkdir -p ~/.dbt
nano ~/.dbt/profiles.yml
```

Configured BigQuery authentication using the `service-account-json` method.

The `profiles.yml` file is excluded from version control to keep credentials secure.

---

## 3. Source Configuration

The project defines the raw datasets in `models/staging/source.yml`.

```yaml
sources:
  - name: raw
    database: <your-gcp-project-id>
    schema: zoomcamp

    tables:
      - name: green_tripdata
      - name: yellow_tripdata
      - name: fhv_tripdata
```

The raw data is stored in the **zoomcamp** dataset in BigQuery.

---

# 🚕 Loading FHV Data with Kestra

Homework Question 6 required loading the **2019 For-Hire Vehicle (FHV)** dataset before building a staging model.

Instead of manually importing the files, I reused and extended the Kestra ingestion pipeline from Module 2.

The workflow **`10_gcp_taxi_scheduled_FHV_data`** supports three taxi types (`yellow`, `green`, and `fhv`). When the `fhv` option is selected, it:

* Downloads the monthly FHV CSV file
* Uploads it to Google Cloud Storage
* Creates an external BigQuery table
* Creates a temporary table with a generated `unique_row_id`
* Merges the records into the partitioned `fhv_tripdata` table

Once the data was available in BigQuery, the `fhv_tripdata` source was added to `source.yml`, allowing dbt to build the `stg_fhv_tripdata` staging model using the same pattern as the existing Green and Yellow taxi models.

---

# ⚙️ dbt Project Configuration

The project uses the following materialization strategy:

```yaml
models:
  my_new_project:
    staging:
      +materialized: view
    intermediate:
      +materialized: table
    marts:
      +materialized: table

vars:
  dev_start_date: '2019-01-01'
  dev_end_date: '2019-02-01'
```

The development variables limit the amount of data processed while developing locally, making dbt runs significantly faster.

For the FHV homework, the project was extended with:

* a new `fhv_tripdata` source
* a new `stg_fhv_tripdata.sql` model
* documentation and tests in the corresponding `schema.yml`

---

# 🛠 Common dbt Commands

```bash
dbt debug
dbt seed
dbt compile
dbt run
dbt test
dbt build
dbt run --full-refresh
dbt run --select <model_name>
dbt ls
```

---

# 💡 Lessons Learned

* Configure `dbt_project.yml` before creating new models.
* Each model folder should have its own `schema.yml`.
* Run `dbt ls` frequently to verify that dbt detects all models.
* Store `profiles.yml` outside the repository because Codespaces can be recreated.
* Use `dbt run --full-refresh` after changing a model's materialization.

---

# 🚕 Module 4 Homework

## 🐳 Question 1 — dbt Lineage

### Task

If you run:

```bash
dbt run --select int_trips_unioned
```

what models will be built?

### Answer

Only `int_trips_unioned`.

To include dependencies:

```bash
dbt run --select +int_trips_unioned
dbt run --select int_trips_unioned+
dbt run --select +int_trips_unioned+
```

---

## 🐳 Question 2 — dbt Tests

### Task

What happens if an `accepted_values` test encounters a value that isn't allowed?

### Answer

The test fails and dbt exits with a non-zero exit code.

---

## 🐳 Question 3 — Monthly Zone Revenue

### Query

```sql
SELECT COUNT(*)
FROM `kestra-project-496118.dbt_dmonteiro_prod.fct_monthly_zone_revenue`
WHERE EXTRACT(YEAR FROM revenue_month) BETWEEN 2019 AND 2020;
```

### Result

11,814

The expected answer was **12,184**.

My dataset differs slightly because it was loaded through my own Kestra pipeline instead of the static homework dataset.

---

## 🐳 Question 4 — Highest Revenue Green Taxi Zone

### Query

```sql
SELECT
    pickup_zone,
    SUM(revenue_monthly_total_amount) AS total_revenue
FROM `kestra-project-496118.dbt_dmonteiro_prod.fct_monthly_zone_revenue`
WHERE service_type = 'Green'
AND EXTRACT(YEAR FROM revenue_month) = 2020
GROUP BY pickup_zone
ORDER BY total_revenue DESC
LIMIT 1;
```

### Answer

**East Harlem North** ($1,817,713.65)

---

## 🐳 Question 5 — Green Taxi Trips (October 2019)

### Query

```sql
SELECT
    SUM(total_monthly_trips) AS total_trips
FROM `kestra-project-496118.dbt_dmonteiro_prod.fct_monthly_zone_revenue`
WHERE service_type = 'Green'
AND EXTRACT(YEAR FROM revenue_month) = 2019
AND EXTRACT(MONTH FROM revenue_month) = 10;
```

### Answer

384,624

---

## 🐳 Question 6 — Build a Staging Model for FHV Data

### Task

Create a staging model for the 2019 **For-Hire Vehicle (FHV)** dataset.

Requirements:

* Load the FHV data into BigQuery
* Filter records where `dispatching_base_num IS NULL`
* Rename columns to follow the project's naming conventions

The raw FHV data was first loaded into BigQuery using the Kestra workflow **`10_gcp_taxi_scheduled_FHV_data`**. After adding `fhv_tripdata` as a dbt source, the `stg_fhv_tripdata` staging model was created following the same design as the existing taxi staging models.

### Query

```sql
SELECT COUNT(*)
FROM `kestra-project-496118.dbt_dmonteiro.stg_fhv_tripdata`;
```

### Answer

**43,244,693**
