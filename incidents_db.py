import logging
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from decouple import config
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine


# Database variables
FILEPATH_DB = Path(__file__).parent / "incidents.db"
URI_SQLITE_DB = f"sqlite+pysqlite:///{FILEPATH_DB}"


def create_db_and_table(url: str):
    """Create database and table."""

    engine = create_engine(url, echo=True, future=True)

    metadata_obj = MetaData()

    incidents = Table(
        "incidents",
        metadata_obj,
        Column("id", Integer, primary_key=True),
        Column("soda_id", String),
        Column("soda_created_at", String),
        Column("soda_updated_at", String),
        Column("soda_version", String),
        Column("crimetype", String),
        Column("datetime", String),
        Column("casenumber", String),
        Column("description", String),
        Column("policebeat", String),
        Column("address", String),
        Column("city", String),
        Column("state", String),
        Column("location_1", String),
        Column("accessed_at", String),
        Column("updated_at", String),
    )

    metadata_obj.create_all(engine)


def get_engine(url: str):
    return create_engine(url, echo=True, future=True)


def config_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        filename="incidents.log",
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )


def update(url: str) -> int:
    """Update database with new incidents since last update. Returns number of new incidents."""

    # API variables
    SODA_APP_TOKEN = config("SODA_APP_TOKEN")
    LIMIT = 100000
    URL = f"https://data.oaklandca.gov/resource/ym6k-rx7a.csv?%24limit={LIMIT}&%24select=%3A*,%20*&%24%24app_token={SODA_APP_TOKEN}"

    # Columns for incidents, less API system columns
    COLUMNS = [
        "crimetype",
        "datetime",
        "casenumber",
        "description",
        "policebeat",
        "address",
        "city",
        "state",
        "location_1",
    ]

    engine = get_engine(url)

    # Get current incidents in database
    current = pd.read_sql("incidents", engine.connect())

    # Get current date and time
    now = datetime.now().isoformat()

    # Get results from api call
    results = pd.read_csv(URL)
    results["accessed_at"] = now
    results["updated_at"] = None
    results = results.rename(
        columns={
            ":id": "soda_id",
            ":created_at": "soda_created_at",
            ":updated_at": "soda_updated_at",
            ":version": "soda_version",
        }
    )

    # Replace nan with None to match what is stored in database
    results = results.fillna(np.nan).replace([np.nan], [None])

    # Combine current and results in order to check for duplicates
    combined = pd.concat([current, results])

    # Drop duplicates and return new incidents
    new = combined.drop_duplicates(subset=COLUMNS, keep="first")
    new = new.loc[new["accessed_at"] == now]

    # Insert into table
    with engine.connect() as conn:
        nrows = new.to_sql("incidents", con=conn, if_exists="append", index=False)
        # logging.info(f"Number of rows: {nrows}")
        conn.commit()

    return nrows


def main():
    config_logging()

    logging.info("Create database and table, if it does not exist.")
    create_db_and_table(URI_SQLITE_DB)

    logging.info("Get incidents and append new incidents to database...")
    nrows = update(URI_SQLITE_DB)
    logging.info(f"Number of rows: {nrows}")

    sys.exit(0)


if __name__ == "__main__":
    main()
