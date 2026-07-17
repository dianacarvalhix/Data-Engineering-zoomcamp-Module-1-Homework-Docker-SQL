/* @bruin
name: staging.trips
type: duckdb.sql
depends:
  - ingestion.trips
  - ingestion.payment_lookup
materialization:
  type: table
  strategy: time_interval
  incremental_key: pickup_datetime
  time_granularity: timestamp
columns:
  - name: vendor_id
    type: integer
  - name: rate_code_id
    type: integer
  - name: pickup_location_id
    type: integer
  - name: dropoff_location_id
    type: integer
  - name: pickup_datetime
    type: timestamp
  - name: dropoff_datetime
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
  - name: payment_type_name
    type: string
  - name: service_type
    type: string
custom_checks:
  - name: row_count_positive
    description: Ensures the table is not empty
    query: SELECT COUNT(*) > 0 FROM staging.trips
    value: 1
@bruin */

WITH ranked_trips AS (
  SELECT
    vendor_id,
    ratecode_id AS rate_code_id,
    pu_location_id AS pickup_location_id,
    do_location_id AS dropoff_location_id,
    CAST(tpep_pickup_datetime AS TIMESTAMP) AS pickup_datetime,
    CAST(tpep_dropoff_datetime AS TIMESTAMP) AS dropoff_datetime,
    store_and_fwd_flag,
    passenger_count,
    trip_distance,
    fare_amount,
    extra,
    mta_tax,
    tip_amount,
    tolls_amount,
    improvement_surcharge,
    total_amount,
    payment_type,
    service_type,
    extracted_at,
    ROW_NUMBER() OVER (
      PARTITION BY
        vendor_id,
        tpep_pickup_datetime,
        tpep_dropoff_datetime,
        pu_location_id,
        do_location_id,
        fare_amount
      ORDER BY extracted_at DESC
    ) AS row_num
  FROM ingestion.trips
  WHERE CAST(tpep_pickup_datetime AS TIMESTAMP) >= '{{ start_datetime }}'
    AND CAST(tpep_pickup_datetime AS TIMESTAMP) < '{{ end_datetime }}'
    AND vendor_id IS NOT NULL
    AND pu_location_id IS NOT NULL
    AND do_location_id IS NOT NULL
    AND passenger_count IS NOT NULL
    AND trip_distance >= 0
    AND fare_amount >= 0
)
SELECT
  vendor_id,
  rate_code_id,
  pickup_location_id,
  dropoff_location_id,
  pickup_datetime,
  dropoff_datetime,
  store_and_fwd_flag,
  passenger_count,
  trip_distance,
  fare_amount,
  extra,
  mta_tax,
  tip_amount,
  tolls_amount,
  improvement_surcharge,
  total_amount,
  payment_type,
  COALESCE(lookup.payment_type_name, 'Unknown') AS payment_type_name,
  service_type
FROM ranked_trips rt
LEFT JOIN ingestion.payment_lookup AS lookup
  ON rt.payment_type = lookup.payment_type_id
WHERE rt.row_num = 1
