# 📌 Overview

This folder contains my work and homework solutions for Module 3 of the Data Engineering Zoomcamp.

In this module I worked with:

* Google Cloud Storage (GCS)
* BigQuery
* External Tables
* Materialized Tables
* Partitioning
* Clustering
* Query Optimization
* Columnar Storage

The goal of the homework was to load NYC Yellow Taxi data (January–June 2024) into Google Cloud Storage, create external and materialized tables in BigQuery, and explore storage optimization techniques such as partitioning and clustering.

---

# 🚕 Module 3 Homework

## Data Loading

The Yellow Taxi Parquet files (January–June 2024) were uploaded to a GCS bucket using the provided Python script.

The data was then made available in BigQuery through an external table and a materialized table.

### External Table

```sql
CREATE OR REPLACE EXTERNAL TABLE `kestra-project-496118.zoomcamp.yellow_taxi_external`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://kestra-zoomcamp-496118/*.parquet']
);
```

### Materialized Table

```sql
CREATE OR REPLACE TABLE `kestra-project-496118.zoomcamp.yellow_taxi`
AS
SELECT *
FROM `kestra-project-496118.zoomcamp.yellow_taxi_external`;
```

---

## 🐳 Question 1 — Counting Records

### Task

What is the count of records for the 2024 Yellow Taxi Data?

### Query

```sql
SELECT COUNT(*)
FROM `kestra-project-496118.zoomcamp.yellow_taxi`;
```

### Answer

20,332,093

---

## 🐳 Question 2 — Data Read Estimation

### Task

Count the distinct number of PULocationIDs for the entire dataset using both the external table and the materialized table.

### Queries

External Table:

```sql
SELECT COUNT(DISTINCT PULocationID)
FROM `kestra-project-496118.zoomcamp.yellow_taxi_external`;
```

Materialized Table:

```sql
SELECT COUNT(DISTINCT PULocationID)
FROM `kestra-project-496118.zoomcamp.yellow_taxi`;
```

### Answer

0 MB for the External Table and 155.12 MB for the Materialized Table.

---

## 🐳 Question 3 — Understanding Columnar Storage

### Task

Why are the estimated bytes different when selecting one column versus two columns?

### Answer

BigQuery uses columnar storage and only scans the columns required by a query. Selecting both `PULocationID` and `DOLocationID` requires reading more data than selecting only `PULocationID`, resulting in a higher number of bytes processed.

---

## 🐳 Question 4 — Counting Zero Fare Trips

### Query

```sql
SELECT COUNT(*)
FROM `kestra-project-496118.zoomcamp.yellow_taxi`
WHERE fare_amount = 0;
```

### Answer

8,333

---

## 🐳 Question 5 — Partitioning and Clustering

### Task

Create an optimized table for queries that filter on `tpep_dropoff_datetime` and order results by `VendorID`.

### Query

```sql
CREATE OR REPLACE TABLE `kestra-project-496118.zoomcamp.yellow_taxi_partitioned`
PARTITION BY DATE(tpep_dropoff_datetime)
CLUSTER BY VendorID AS
SELECT *
FROM `kestra-project-496118.zoomcamp.yellow_taxi`;
```

### Answer

Partition by `tpep_dropoff_datetime` and cluster by `VendorID`.

Partitioning allows BigQuery to scan only the relevant date partitions, while clustering organizes data by VendorID within each partition, improving query efficiency.

---

## 🐳 Question 6 — Partition Benefits

### Query

```sql
SELECT DISTINCT VendorID
FROM `kestra-project-496118.zoomcamp.yellow_taxi`
WHERE tpep_dropoff_datetime BETWEEN '2024-03-01'
AND '2024-03-15 23:59:59';
```

and

```sql
SELECT DISTINCT VendorID
FROM `kestra-project-496118.zoomcamp.yellow_taxi_partitioned`
WHERE tpep_dropoff_datetime BETWEEN '2024-03-01'
AND '2024-03-15 23:59:59';
```

### Answer

310.24 MB for the non-partitioned table and 26.84 MB for the partitioned table.

---

## 🐳 Question 7 — External Table Storage

### Answer

The data is stored in the GCS bucket.

The external table contains only metadata and references the Parquet files stored in Cloud Storage.

---

## 🐳 Question 8 — Clustering Best Practices

### Answer

False.

Clustering should only be applied when it matches query patterns. It is not a best practice to cluster every table.

---

## 🐳 Question 9 — Understanding Table Scans

### Query

```sql
SELECT COUNT(*)
FROM `kestra-project-496118.zoomcamp.yellow_taxi`;
```

### Answer

Estimated bytes processed: 0 B.

BigQuery can answer a simple `COUNT(*)` query using table metadata without scanning the underlying data.
