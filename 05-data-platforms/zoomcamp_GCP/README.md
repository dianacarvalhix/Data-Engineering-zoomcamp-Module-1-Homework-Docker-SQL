# Bruin BigQuery Migration

This folder contains a BigQuery-based version of the DuckDB Bruin pipeline from the sibling folder.

## What changed

- Replaced the DuckDB connection with a Google Cloud Platform connection named `gcp-default`.
- Switched the seed, SQL, and Python assets to use BigQuery-compatible asset types and connection settings.
- Added a `.bruin.yml` file that reads the service account JSON from the `GCP_SERVICE_ACCOUNT_JSON` environment variable.
- Added a `.env.example` template for local configuration.

## Manual steps required

1. Create or select a GCP project and enable the BigQuery API.
2. Create a service account in GCP IAM & Admin > Service Accounts and download the JSON key.
3. Create the BigQuery datasets `ingestion`, `staging`, and `reports` in the target project if they do not already exist.
4. Copy `.env.example` to `.env` and fill in `GCP_SERVICE_ACCOUNT_JSON` with the downloaded key contents.
5. In Bruin Cloud, set the same environment variable in the connection settings for the pipeline environment.
6. Run validation and execution from this folder.

## Validation

```bash
cd /workspaces/Data-Engineering-zoomcamp-Module-1-Homework-Docker-SQL/05-data-platforms/zoomcamp_GCP
bruin validate .
```

## Notes

- BigQuery needs datasets to exist before Bruin writes to them. The suggested dataset names are `ingestion`, `staging`, and `reports`.
- Bruin may create tables automatically inside those datasets, but the datasets themselves usually need to be created manually in GCP first.
- The original DuckDB version in the sibling folder was left unchanged.
