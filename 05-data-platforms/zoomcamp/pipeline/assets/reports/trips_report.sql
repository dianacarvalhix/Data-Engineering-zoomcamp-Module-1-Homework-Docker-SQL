/* @bruin

# Docs:
# - SQL assets: https://getbruin.com/docs/bruin/assets/sql
# - Materialization: https://getbruin.com/docs/bruin/assets/materialization
# - Quality checks: https://getbruin.com/docs/bruin/quality/available_checks

name: reports.trips_report
type: duckdb.sql

depends:
  - staging.trips

materialization:
  type: table
  strategy: time_interval
  incremental_key: trip_date
  time_granularity: timestamp

columns:
  - name: trip_date
    type: date
    description: Pickup date for the trip aggregation
    primary_key: true
  - name: service_type
    type: string
    description: Taxi service type
    primary_key: true
  - name: payment_type_name
    type: string
    description: Payment type label
    primary_key: true
  - name: trip_count
    type: bigint
    description: Number of trips in the aggregated bucket
    checks:
      - name: non_negative
  - name: total_amount
    type: numeric
    description: Sum of total fares for the aggregated bucket
    checks:
      - name: non_negative

@bruin */

SELECT
  CAST(DATE(pickup_datetime) AS DATE) AS trip_date,
  service_type,
  payment_type_name,
  COUNT(*) AS trip_count,
  SUM(total_amount) AS total_amount
FROM staging.trips
WHERE pickup_datetime >= '{{ start_datetime }}'
  AND pickup_datetime < '{{ end_datetime }}'
GROUP BY
  CAST(DATE(pickup_datetime) AS DATE),
  service_type,
  payment_type_name
