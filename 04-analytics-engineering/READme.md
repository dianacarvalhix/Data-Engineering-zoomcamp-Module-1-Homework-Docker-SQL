# Analysis folder is usually used for data quality reports. Or to place SQL files that are not intended to be exposed.

# dbt_project.yml is needed to run dbt commands.

# macros behave like python functions (reusable logic). They allow to encapsulate logic in one place.

# seeds -A space to upload csv and flat files to add to dbt later.

# snapshots - take a picture of a table at a moment in time. Useful to track the history of a column that overwrites itself.

# tests - A place to put assertions in SQL format. A place for singular tests, if the sql command returns more than 0 rows, the dbt build fails.


# models :
    sources: sources (raw table from database
    staging: files are 1 to 1 copy of data with minimal cleaning steps (data types, renaming columns)
    intermediate - nice for heavy duty cleaning or complex logic
    marts- If it is in marts, it is ready for consumption, these ones should be the ones exposed. Tables ready for dashboards, properly modeled, clean tables.