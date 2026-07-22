# 📌 Module 5 — Data Platforms (Bruin) — NYC Taxi Pipeline

## Overview

This module builds an end-to-end NYC Taxi data pipeline using [Bruin](https://getbruin.com), following a three-layer architecture:

```
ingestion  →  staging  →  reports
```

- **ingestion**: raw data loaded as-is (append-only), no cleaning
- **staging**: deduplicated, cleaned, and enriched (joins in lookup data)
- **reports**: aggregated data ready for analysis/BI

Three versions of the pipeline exist in this repo:

| Folder | Description |
|---|---|
| `bruin-pipeline/` | Chess.com example pipeline, used to learn Bruin basics |
| `zoomcamp/pipeline/` | Manually built NYC Taxi pipeline, DuckDB destination |
| `zoomcampAutomated/pipeline/` | Same NYC Taxi pipeline, built end-to-end via an AI agent (Copilot + Bruin MCP) from a single prompt |
| `zoomcamp_GCP/pipeline/` | NYC Taxi pipeline migrated to BigQuery, so it can run on Bruin Cloud |

---

## 1. Setting up Bruin MCP (VS Code)

The course instructions were originally written for Cursor, which uses a different config format than VS Code. To set it up in VS Code:

1. Confirm the Bruin CLI is installed and on your PATH:
   ```bash
   bruin version
   ```
2. Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) → **`MCP: Open User Configuration`** (or create `.vscode/mcp.json` for a project-only setup).
3. Add the following (note: VS Code uses `"servers"`, not `"mcpServers"` like Cursor):
   ```json
   {
     "servers": {
       "bruin": {
         "type": "stdio",
         "command": "bruin",
         "args": ["mcp"]
       }
     },
     "inputs": []
   }
   ```
4. Reload VS Code (`Developer: Reload Window`).
5. Command Palette → **`MCP: List Servers`** → select `bruin` → **Start** if it shows as "Stopped".
   - If it fails to start, check **Show Output** for errors (commonly: `bruin` not on PATH, or no Bruin project open in the workspace).

Once running, GitHub Copilot Chat (in **Agent mode**) can call Bruin's tools directly — inspecting the project, running commands, and looking up documentation — instead of just suggesting text.

### What is MCP?

MCP (Model Context Protocol) is a standard that lets an AI assistant call external tools instead of only generating text. An **MCP server** (here, Bruin) exposes specific capabilities; an **MCP client** (VS Code / Copilot Chat) connects to it and lets the AI use those tools when relevant. It's the mechanism that turns "the AI can talk about my pipeline" into "the AI can actually run and inspect my pipeline."

---

## 2. Project structure & `.bruin.yml`

A Bruin **project** is scoped to the Git repository, not a subfolder. `.bruin.yml` (holding connection credentials) lives at the **repository root**, not inside individual pipeline folders — Bruin auto-discovers it there and scans the whole repo for any `pipeline.yml` files, however deeply nested.

- It's auto-created (and auto-gitignored) the first time you run `bruin run` or `bruin validate` if it doesn't already exist.
- All pipelines in this repo (chess, zoomcamp, zoomcampAutomated) share the same root-level `.bruin.yml` — no need for one per pipeline.

Example local connections block (DuckDB):
```yaml
connections:
  duckdb:
    - name: "duckdb-default"
      path: "duckdb.db"
  chess:
    - name: "chess-default"
      players: [...]
```

---

## 3. The `zoomcamp` template

`bruin init zoomcamp <folder-name>` scaffolds a **TODO-based learning exercise** for building an NYC Taxi pipeline — unlike the `chess` template (which comes fully pre-built and runnable), this one intentionally ships incomplete: no `.bruin.yml`, and asset files full of `# TODO` comments to fill in yourself.

---

## 4. Pipeline assets

### `ingestion/trips.py` — Python asset

- Fetches NYC TLC public trip data directly from `https://d37ci6vzurychx.cloudfront.net/trip-data/`, one Parquet file per `(month, taxi_type)`.
- No API key required — the TLC data is fully public.
- Uses `BRUIN_START_DATE` / `BRUIN_END_DATE` (from `--start-date`/`--end-date`) to loop month by month, and `BRUIN_VARS` (from `--var`) to read the `taxi_types` list.
- Adds `service_type` and `extracted_at` metadata columns, then returns one combined DataFrame.
- **Materialization**: `type: table`, `strategy: append` — every run just adds more rows. Deduplication is intentionally *not* handled here; it's handled downstream in staging. This keeps ingestion simple and resilient (safe to re-run without special logic).

**⚠️ Gotcha — column name casing**: the raw parquet files use TLC's original camelCase column names (`VendorID`, `PULocationID`, etc.), but Bruin's write process into DuckDB automatically **normalizes column names to snake_case** (`vendor_id`, `pu_location_id`, etc.) on the way in. The `columns:` metadata block in the asset file does **not** auto-update to reflect this — it's just documentation you write by hand, and it will silently drift out of sync with the real table unless you keep it updated manually. Always verify actual column names with:
```bash
bruin query --connection duckdb-default --query "describe ingestion.trips"
```

### `ingestion/payment_lookup.asset.yml` — Seed asset

- Loads a small static CSV (`payment_lookup.csv`, mapping `payment_type_id` → `payment_type_name`) directly into a table.
- **This runs independently of `trips.py`** — it does not touch or merge with `ingestion.trips`. It creates a completely separate table (`ingestion.payment_lookup`), joined against `trips` later, in staging.
- Runs quality checks after loading (`not_null`, `unique` on the primary key).

### `staging/trips.sql` — SQL asset

- Depends on both `ingestion.trips` and `ingestion.payment_lookup`.
- **Deduplicates** rows using `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY extracted_at DESC)`, keeping only the most recently extracted copy of each apparent duplicate trip (this is the fix for `append`-only ingestion potentially loading the same row twice across re-runs).
- Filters out rows with missing key fields or negative fares/distances (basic data quality cleaning).
- **Joins** with `ingestion.payment_lookup` to turn the numeric `payment_type` into a readable `payment_type_name`, defaulting to `'Unknown'` if no match is found.
- **Materialization**: `strategy: time_interval`, `incremental_key: pickup_datetime` — only deletes and rebuilds the specific date window being processed, not the whole table.

**Known real-data quirk**: one of the default template's chess-style examples (a `not_null` check failing on a `name` column) has an equivalent lesson here — TLC data isn't perfectly clean, which is exactly why the `WHERE` clause filters and the dedup logic exist.

### `reports/trips_report.sql` — SQL asset

- Depends on `staging.trips`.
- **Aggregates** individual trip rows into daily summary buckets, grouped by `(trip_date, service_type, payment_type_name)`, computing `trip_count` and `total_amount` (sum of fares) per group.
- `trip_date` is derived from `pickup_datetime` via `DATE(pickup_datetime)` — it does **not** exist as a column in `staging.trips`; it's created fresh in this query.
- **Materialization**: `strategy: time_interval`, `incremental_key: trip_date`, `time_granularity: date` (not `timestamp`, since `trip_date` only has day-level precision).

---

## 5. Running the pipeline

### First run (tables don't exist yet)

`time_interval` strategy works by running `DELETE FROM <table> WHERE <incremental_key> BETWEEN ...` before inserting fresh data. This fails if the table doesn't exist yet — so the **first run always needs `--full-refresh`**, which skips the delete step and builds the table from scratch:

```bash
bruin run --full-refresh --start-date 2022-01-01 --end-date 2022-01-31 --var 'taxi_types=["yellow"]'
```

### Subsequent runs (any new date range)

Once the tables exist, `--full-refresh` is **not** needed for new date ranges — even ranges never run before. The `DELETE ... WHERE` simply matches nothing for an unprocessed window, then inserts normally:

```bash
bruin run --start-date 2022-02-01 --end-date 2022-02-28 --var 'taxi_types=["yellow"]'
```

Use `--full-refresh` again only if: the table doesn't exist yet in a given environment (e.g. first run in Bruin Cloud, or a fresh database), you changed the transformation logic and want history recomputed, or something needs to be rebuilt from scratch.

### Running without explicit dates

Plain `bruin run` defaults to **today's date** as the interval — only useful for a pipeline actually deployed on a live daily schedule, not for backfilling historical months.

---

## 6. Debugging notes / gotchas encountered

- **Two duplicate `duckdb.db` files** appeared in the repo because `bruin run` was executed from two different working directories at different times — each created its own DB file relative to wherever it was invoked from. Always check `find . -iname "*.db"` if queries seem to return unexpected/missing data.
- **`duckdb.db` must never be committed to Git** — it's a generated data file, not source code, and can easily exceed GitHub's 100MB file size limit (it hit 357MB here). Add `*.db` to `.gitignore`. If it's already been committed, remove it with `git rm --cached <file>` and amend the commit *before* pushing.
- **The `duckdb` CLI ≠ the `duckdb` Python package.** `pip install duckdb` only gives you the Python library (`import duckdb`), not a standalone terminal command. To query the database from the terminal, either use Python (`duckdb.connect('duckdb.db')`), or Bruin's own built-in query command:
  ```bash
  bruin query --connection duckdb-default --query "select * from ingestion.trips limit 5"
  ```
---

## 7. Automating the build with an AI agent (MCP)

After building the pipeline manually, the same end-to-end pipeline was rebuilt automatically by an AI agent (GitHub Copilot, Agent mode) using Bruin's MCP tools, given a single detailed prompt specifying the architecture, source details, and validation steps. This produced the `zoomcampAutomated/` pipeline, and it ran successfully with all quality checks passing.

This is a useful reflection point: the agent could execute the build quickly, but only because the underlying design decisions (layer architecture, incremental strategy per layer, dedup logic, what counts as "clean" data) had already been worked out by hand first. The manual build was what made it possible to write a prompt precise enough for the agent to succeed — and to recognize whether its output was actually correct.

---

## 8. Deploying to Bruin Cloud

### Connecting the project
- Bruin Cloud syncs pipelines from a **Git repository**, added under **Team Settings → Projects** (not just a GitHub account connection/auth step — those are two separate things).
- Point it at the **repository root**, not a specific module subfolder — Bruin scans the whole repo tree for any `pipeline.yml` files, same as the local CLI.
- Pipelines synced from a repo start **disabled by default** — check Catalog → Pipelines and enable them explicitly.
- Nothing gets pushed to Bruin Cloud until it's actually pushed to **GitHub** — local, uncommitted work is invisible to it.

### DuckDB doesn't work as a Bruin Cloud destination
DuckDB is a local, single-process, embedded database (just a file on disk) — it isn't designed for Bruin Cloud's ephemeral, pod-based execution environment, which has no persistent disk for a DuckDB file to live on between runs. This is why **DuckDB does not appear as a connection type option in Bruin Cloud** at all. The cloud-native equivalent is **MotherDuck**, but this project instead migrated to **BigQuery**, reusing an existing GCP project.

### Migrating to BigQuery (`zoomcamp_GCP/`)
- All asset `type:` fields changed from `duckdb.sql`/`duckdb.seed` to their BigQuery equivalents.
- All `connection:` references updated to a new `gcp-default` connection (`google_cloud_platform` type), instead of the DuckDB one.
- `pipeline.yml`'s `default_connections` updated accordingly.
- **Credentials are never hardcoded** into `.bruin.yml`. Instead, it references an environment variable:
  ```yaml
  connections:
    google_cloud_platform:
      - name: "gcp-default"
        project_id: "kestra-project-496118"
        service_account_json: "${GCP_SERVICE_ACCOUNT_JSON}"
  ```
  The `${...}` syntax tells Bruin to read the value from an environment variable at runtime, rather than storing the actual service account key (a real credential) in a file that could end up in version control.

- **Local setup**: the real credential lives in a `.env` file (gitignored, kept at the project root alongside `.bruin.yml` for visibility) containing:
  ```
  GCP_SERVICE_ACCOUNT_JSON={"type": "service_account", "project_id": "...", ...}
  ```
- **Before running locally**, that value must be loaded into the terminal session's environment (this only needs to be done once per new terminal session — it is *not* persistent and must be re-run if you open a fresh terminal):
  ```bash
  export GCP_SERVICE_ACCOUNT_JSON="$(python - <<'PY'
  from pathlib import Path
  p = Path('/workspaces/Data-Engineering-zoomcamp-Module-1-Homework-Docker-SQL/05-data-platforms/zoomcamp_GCP/.env')
  for line in p.read_text().splitlines():
      if line.startswith('GCP_SERVICE_ACCOUNT_JSON='):
          print(line.split('=', 1)[1].strip())
          break
  PY
  )"
  ```
  This only sets an in-memory environment variable for the current shell session — it does not write or create any file on disk, so it introduces no additional risk of committing secrets to Git.
- **In Bruin Cloud**, the same service account JSON is pasted directly into the connection's settings in the UI — Cloud has no access to the local `.env` file at all; the two environments are completely separate.

### Local vs Cloud data are separate
Running locally and running in Bruin Cloud use **completely independent databases**, even though both were initially configured as "DuckDB." Local runs write to `duckdb.db` on the Codespace's disk; Bruin Cloud runs (before the BigQuery migration) would have used its own separate DuckDB file inside its own execution environment — data loaded in one is invisible to the other. This is a normal dev-vs-production pattern.

### Triggering a manual run in Bruin Cloud
Bruin Cloud's "Trigger a new pipeline run" dialog mirrors the local CLI flags:
- **Full Refresh** checkbox = `--full-refresh`
- **Start Date / End Date** = `--start-date` / `--end-date` (defaults to today if left unchanged — same "today's date" pitfall as running `bruin run` locally with no dates)
- **Variables** section = `--var`

### Debugging one Cloud-specific error
`connection 'duckdb-default' is not a duckdb connection` — this happened because a connection *named* `duckdb-default` had actually been created under the `google_cloud_platform` type by mistake (name and type are set independently when creating a connection; a matching name doesn't guarantee a matching type). Fixed by deleting the misconfigured connection and creating the correctly-typed one.

---



# 🐳 Module 5 Homework

## 🐳 Question 1 — Bruin Pipeline Structure

### Task

Which files are required in a Bruin project?

### Answer

`pipeline.yml` and the pipeline assets.

---

## 🐳 Question 2 — Materialization Strategy

### Task

Which strategy incrementally rebuilds data for a specific time interval?

### Answer

`time_interval`

---

## 🐳 Question 3 — Pipeline Variables

### Task

How can pipeline variables be overridden to process only Yellow Taxi data?

### Command

```bash
bruin run --var 'taxi_types=["yellow"]'
```

---

## 🐳 Question 4 — Running Dependencies

### Task

Run an asset together with all downstream dependencies.

### Command

```bash
bruin run ingestion/trips.py --downstream
```

---

## 🐳 Question 5 — Quality Checks

### Task

Ensure `pickup_datetime` never contains NULL values.

### Answer

```yaml
name: not_null
```

---

## 🐳 Question 6 — Lineage

### Task

Visualize the dependency graph.

### Command

```bash
bruin lineage
```

---

## 🐳 Question 7 — First-Time Execution

### Task

Which flag should be used when running the pipeline for the first time?

### Answer

```bash
--full-refresh
```