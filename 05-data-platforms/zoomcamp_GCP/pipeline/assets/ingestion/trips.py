"""@bruin

name: ingestion.trips
type: python
image: python:3.11
connection: gcp-default

materialization:
  type: table
  strategy: append

columns:
  - name: vendor_id
    type: integer
    description: Taxi technology provider (1 = Creative Mobile Technologies, 2 = VeriFone Inc.)

  - name: ratecode_id
    type: integer
    description: Rate code at end of trip (1=Standard, 2=JFK, 3=Newark, 4=Nassau/Westchester, 5=Negotiated, 6=Group)

  - name: pu_location_id
    type: integer
    description: TLC Taxi Zone where the meter was engaged

  - name: do_location_id
    type: integer
    description: TLC Taxi Zone where the meter was disengaged

  - name: tpep_pickup_datetime
    type: timestamp
    description: Date and time when the meter was engaged

  - name: tpep_dropoff_datetime
    type: timestamp
    description: Date and time when the meter was disengaged

  - name: store_and_fwd_flag
    type: string
    description: Flag indicating if the trip record was held in vehicle memory before being sent to the vendor (Y/N)

  - name: passenger_count
    type: integer
    description: Number of passengers in the vehicle (driver-entered value)

  - name: trip_distance
    type: numeric
    description: Trip distance in miles reported by the taximeter

  - name: fare_amount
    type: numeric
    description: Time and distance fare calculated by the meter

  - name: extra
    type: numeric
    description: Miscellaneous extras and surcharges (rush hour, overnight, etc.)

  - name: mta_tax
    type: numeric
    description: $0.50 MTA tax automatically triggered based on the meter rate

  - name: tip_amount
    type: numeric
    description: Tip amount (credit card tips only; cash tips are not included)

  - name: tolls_amount
    type: numeric
    description: Total amount of all tolls paid during the trip

  - name: improvement_surcharge
    type: numeric
    description: Improvement surcharge assessed on hailed trips

  - name: total_amount
    type: numeric
    description: Total amount charged to passengers (does not include cash tips)

  - name: payment_type
    type: integer
    description: Payment method code (1=Credit card, 2=Cash, 3=No charge, 4=Dispute, 5=Unknown, 6=Voided)

  - name: service_type
    type: string
    description: Taxi service type (Yellow or Green).

  - name: extracted_at
    type: timestamp
    description: Timestamp when the data was extracted from the TLC public data source.
@bruin"""

from datetime import datetime, UTC
import json
import os

import pandas as pd


def materialize():
    """
    Fetch NYC Taxi trip data from TLC public endpoint.

    This ingestion asset:
    - Uses BRUIN_START_DATE and BRUIN_END_DATE to determine date range
    - Reads `taxi_types` from BRUIN_VARS to determine which taxi types to ingest
    - Fetches parquet files from the TLC public endpoint
    - Adds metadata columns for lineage
    """

    start_date_str = os.getenv("BRUIN_START_DATE")
    end_date_str = os.getenv("BRUIN_END_DATE")
    bruin_vars_json = os.getenv("BRUIN_VARS", "{}")

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=UTC)
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").replace(tzinfo=UTC)

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
                print(f"Warning: Failed to fetch {url}")
                print(e)

        if month == 12:
            current_date = datetime(year + 1, 1, 1, tzinfo=UTC)
        else:
            current_date = datetime(year, month + 1, 1, tzinfo=UTC)

    if not dataframes:
        print("Warning: No data fetched. Returning empty DataFrame.")
        return pd.DataFrame()

    return pd.concat(dataframes, ignore_index=True)
