"""@bruin

name: ingestion.trips
type: python
image: python:3.11
connection: duckdb-default
materialization:
  type: table
  strategy: append
columns:
  - name: vendor_id
    type: integer
  - name: ratecode_id
    type: integer
  - name: pu_location_id
    type: integer
  - name: do_location_id
    type: integer
  - name: tpep_pickup_datetime
    type: timestamp
  - name: tpep_dropoff_datetime
    type: timestamp
  - name: store_and_fwd_flag
    type: string
  - name: passenger_count
    type: integer
  - name: trip_distance
    type: numeric
  - name: fare_amount
    type: numeric
  - name: extra
    type: numeric
  - name: mta_tax
    type: numeric
  - name: tip_amount
    type: numeric
  - name: tolls_amount
    type: numeric
  - name: improvement_surcharge
    type: numeric
  - name: total_amount
    type: numeric
  - name: payment_type
    type: integer
  - name: service_type
    type: string
  - name: extracted_at
    type: timestamp
@bruin"""

from datetime import datetime, UTC
from dateutil.relativedelta import relativedelta
import json
import os

import pandas as pd


def materialize():
    start_date_str = os.getenv("BRUIN_START_DATE")
    end_date_str = os.getenv("BRUIN_END_DATE")
    bruin_vars_json = os.getenv("BRUIN_VARS", "{}")

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    bruin_vars = json.loads(bruin_vars_json)
    taxi_types = bruin_vars.get("taxi_types", ["yellow"])

    base_url = "https://d37ci6vzurychx.cloudfront.net/trip-data/"
    dataframes = []
    current_date = start_date
    extracted_at = datetime.now(UTC)

    while current_date <= end_date:
        year = current_date.year
        month = current_date.month
        for taxi_type in taxi_types:
            filename = f"{taxi_type}_tripdata_{year:04d}-{month:02d}.parquet"
            url = f"{base_url}{filename}"
            try:
                print(f"Fetching: {url}")
                df = pd.read_parquet(url)
                df["service_type"] = taxi_type.capitalize()
                df["extracted_at"] = extracted_at
                dataframes.append(df)
            except Exception as e:
                print(f"Warning: Failed to fetch {url}: {e}")
        current_date += relativedelta(months=1)

    if not dataframes:
        return pd.DataFrame()

    return pd.concat(dataframes, ignore_index=True)
