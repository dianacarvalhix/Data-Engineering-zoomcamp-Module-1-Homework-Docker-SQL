#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from sqlalchemy import create_engine
from tqdm.auto import tqdm
import click


@click.command()
@click.option('--pg-user', default='root', help='PostgreSQL username')
@click.option('--pg-pass', default='root', help='PostgreSQL password')
@click.option('--pg-host', default='localhost', help='PostgreSQL host')
@click.option('--pg-port', default='5432', help='PostgreSQL port')
@click.option('--pg-db', default='ny_taxi', help='PostgreSQL database name')
@click.option('--year', default=2025, type=int, help='Year of the data')
@click.option('--month', default=11, type=int, help='Month of the data')
@click.option('--chunksize', default=100000, type=int, help='Chunk size for ingestion')
@click.option('--target-table', default='green_taxi_trips', help='Target table name')

def run(pg_user, pg_pass, pg_host, pg_port, pg_db, year, month, chunksize, target_table):

    # Parquet URL
    url = f'https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_{year}-{month:02d}.parquet'

    # Create DB connection
    engine = create_engine(f'postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}')

    # Read full parquet file
    df = pd.read_parquet(url)

    # Optional but good practice
    df.columns = df.columns.str.lower()

    # Chunking manually
    n = len(df)

    for i in tqdm(range(0, n, chunksize)):
        df_chunk = df.iloc[i:i + chunksize]

        if i == 0:
            # Create table schema
            df_chunk.head(0).to_sql(
                name=target_table,
                con=engine,
                if_exists='replace',
                index=False
            )

        # Append data
        df_chunk.to_sql(
            name=target_table,
            con=engine,
            if_exists='append',
            index=False
        )

    zone_url = "https://github.com/DataTalksClub/nyc-tlc-data/releases/download/misc/taxi_zone_lookup.csv"

    df_zones = pd.read_csv(zone_url)

    df_zones.to_sql(
        name='taxi_zone_lookup',
        con=engine,
        if_exists='replace',
        index=False
    )



if __name__ == '__main__':
    run()


