# Data-Engineering-zoomcamp-Module-1-Homework-Docker-SQL
📌 Overview

This repository contains my solutions for Module 1 of the Data Engineering Zoomcamp.
The exercises focus on using Docker, working with Python images, and understanding containerized environments.



🐳 Question 1 – Understanding Docker Images
Task: 

Run the official Python 3.13 Docker image and check the installed pip version.

###Answer
Command used:
docker run -it --entrypoint bash python:3.13
Inside the container:
pip --version
Output observed:
pip 26.0.1 from /usr/local/lib/python3.13/site-packages/pip (python 3.13)
Answer selected

Even though the observed version was 26.0.1, the expected answer from the course options is 24.3.1 as the official docker image may contain a newer pip version than the one used in the course material.

🐳 Question 2. Understanding Docker networking and docker-compose
Task: 

Given the following docker-compose.yaml, what is the hostname and port that pgadmin should use to connect to the postgres database?

services:
  db:
    container_name: postgres
    image: postgres:17-alpine
    environment:
      POSTGRES_USER: 'postgres'
      POSTGRES_PASSWORD: 'postgres'
      POSTGRES_DB: 'ny_taxi'
    ports:
      - '5433:5432'
    volumes:
      - vol-pgdata:/var/lib/postgresql/data

  pgadmin:
    container_name: pgadmin
    image: dpage/pgadmin4:latest
    environment:
      PGADMIN_DEFAULT_EMAIL: "pgadmin@pgadmin.com"
      PGADMIN_DEFAULT_PASSWORD: "pgadmin"
    ports:
      - "8080:80"
    volumes:
      - vol-pgadmin_data:/var/lib/pgadmin

volumes:
  vol-pgdata:
    name: vol-pgdata
  vol-pgadmin_data:
    name: vol-pgadmin_data

###Answer
db:5432

### Explanation
- Docker Compose creates a network where each service is accessible by its service name
- The Postgres service is named `db`, so this becomes the hostname
- Port 5432 is the internal Postgres port used for container-to-container communication

### Note
`postgres:5432` may also work due to the `container_name`, but using the service name (`db`) is the recommended and standard approach.


For the questions questions 3, 4, 5 and 6 it was built a data ingestion pipeline using Docker, PostgreSQL, and Python to analyze NYC taxi trip data. I intentionally took a more complex approach to this assignment to practice Docker and pipeline design.

Instead of solving it with a simple script or notebook, I built a containerized pipeline with PostgreSQL, pgAdmin, and a Python ingestion service.

This helped me understand how real-world data pipelines are structured and how services communicate in a Docker environment.

🧱 Architecture
PostgreSQL (database)
pgAdmin (UI)
Python ingestion script (ingest_green.py)
Docker + Docker Compose

📁 Project Structure
ingest_green.py → loads parquet data into PostgreSQL
Dockerfile → builds ingestion environment using uv
docker-compose.yml → runs database + ingestion + pgAdmin
pyproject.toml → dependencies
uv.lock → locked versions
.venv/ → local dev environment (not used in Docker)

⚙️ How to Run
docker compose up --build

🐳 Question 3. Counting short trips

Task:
For the trips in November 2025 (lpep_pickup_datetime between '2025-11-01' and '2025-12-01', exclusive of the upper bound), how many trips had a trip_distance of less than or equal to 1 mile?


    7,853
    8,007
    8,254
    8,421

### Resolution
SELECT COUNT(*) 
FROM green_taxi_trips
WHERE lpep_pickup_datetime >= '2025-11-01'
  AND lpep_pickup_datetime < '2025-12-01'
  AND trip_distance <= 1;

### Result:8007

🐳 Question 4. Longest trip for each day

Task:
Which was the pick up day with the longest trip distance? Only consider trips with trip_distance less than 100 miles (to exclude data errors).

Use the pick up time for your calculations.

    2025-11-14
    2025-11-20
    2025-11-23
    2025-11-25

### Resolution

SELECT 
    DATE(lpep_pickup_datetime) AS pickup_day,
    MAX(trip_distance) AS max_distance
FROM green_taxi_trips
WHERE trip_distance < 100
GROUP BY pickup_day
ORDER BY max_distance DESC
LIMIT 1;

### Result
2025-11-14

🐳 Question 5. Biggest pickup zone

Task:
Which was the pickup zone with the largest total_amount (sum of all trips) on November 18th, 2025?


    East Harlem North
    East Harlem South
    Morningside Heights
    Forest Hills



### Resolution

SELECT 
    z."Zone",
    SUM(t.total_amount) AS total
FROM green_taxi_trips t
JOIN taxi_zone_lookup z
  ON t."pulocationid" = z."LocationID"
WHERE DATE(t.lpep_pickup_datetime) = '2025-11-18'
GROUP BY z."Zone"
ORDER BY total DESC
LIMIT 1;

### Result
East Harlem North


🐳 Question 6. Longest trip for each day

For the passengers picked up in the zone named "East Harlem North" in November 2025, which was the drop off zone that had the largest tip?

Note: it's tip , not trip. We need the name of the zone, not the ID.

    JFK Airport
    Yorkville West
    East Harlem North
    LaGuardia Airport

### Resolution
SELECT 
    z."Zone",
    SUM(t.total_amount) AS total
FROM green_taxi_trips t
JOIN taxi_zone_lookup z
  ON t."pulocationid" = z."LocationID"
WHERE DATE(t.lpep_pickup_datetime) = '2025-11-18'
GROUP BY z."Zone"
ORDER BY total DESC
LIMIT 1;

### Result
Yorkville West
