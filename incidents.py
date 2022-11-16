import logging
from pathlib import Path
from urllib.parse import quote

import geopandas
import pandas as pd
from decouple import config
from sqlalchemy import create_engine

from incidents_db import config_logging
from send_email import send_email

if __name__ == "__main__":

    # Start logger
    config_logging(level=logging.INFO)

    MAPBOX_TOKEN = config("MAPBOX_TOKEN")
    FILEPATH_DB = Path(__file__).parent / "incidents.db"
    URI_SQLITE_DB = f"sqlite+pysqlite:///{FILEPATH_DB}"

    # Marker style
    marker = {
        "assault": {"color": "#a83232", "symbol": "baseball"},
        "burglary": {"color": "#000000", "symbol": "baseball"},
        "vehicle": {"color": "#8132a8", "symbol": "car"},
        "weapons": {"color": "#00ffd5", "symbol": "car"},
        "robbery": {"color": "#001999", "symbol": "car"},
        "vandalism": {"color": "#ff9d00", "symbol": "car"},
        "theft": {"color": "#20422f", "symbol": "car"},
    }

    engine = create_engine(URI_SQLITE_DB, echo=True, future=True)

    # Get incidents table
    incidents = pd.read_sql("incidents", engine.connect())

    # Get last date and time the table was appended with new incidents
    last_access = list(incidents["accessed_at"].unique())
    last_access.sort()
    last_access = last_access[-1]

    # Get last appended incidents
    recent = incidents.loc[incidents["accessed_at"] == last_access]
    recent = recent.sort_values(by=["datetime"])

    # Convert the dataframe to a geodataframe
    recent_gs = geopandas.GeoSeries.from_wkt(recent["location_1"])
    recent_gdf = geopandas.GeoDataFrame(recent, geometry=recent_gs, crs="EPSG:4326")

    # Get list of geojson files for areas of interest
    aoi_list = list((Path(__file__).parent / "data").glob("*.geojson"))

    # Get most recent appended incidents for each area of interest
    for aoi in aoi_list:
        temp_aoi = geopandas.read_file(aoi)
        # Intersect incidents with coordinates and aoi
        recent_aoi = geopandas.overlay(recent_gdf.loc[recent_gdf["geometry"].notna()], temp_aoi, how="intersection")
        logging.info(f"Incidents in {aoi.stem}: {len(recent_aoi)}")

        # If there are incidents, prepare email
        if len(recent_aoi) > 0:
            # Add marker color
            for incident_type in marker.keys():
                recent_aoi.loc[
                    recent_aoi["crimetype"].str.contains(
                        incident_type, case=False, na=False
                    ),
                    "marker-color",
                ] = marker[incident_type]["color"]

            recent_aoi["marker-symbol"] = range(1, len(recent_aoi) + 1)
            recent_aoi["marker-symbol"] = recent_aoi["marker-symbol"].astype(str)

            # Construct url
            # Filter for select columns
            geojson = recent_aoi[
                [
                    "marker-color",
                    "marker-symbol",
                    "geometry",
                ]
            ].to_json(drop_id=True)

            url = f"https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/geojson({quote(geojson)})/auto/900x900?access_token={MAPBOX_TOKEN}"

            # Send email
            email_recent = recent_aoi[
                [
                    "marker-symbol",
                    "casenumber",
                    "crimetype",
                    "datetime",
                    "description",
                    "address",
                ]
            ]

            try:
                send_email(
                    subject="Incidents",
                    body=aoi.stem,
                    table_html=email_recent.to_html(index=False),
                    image_url=url,
                )
                logging.info(
                    f"Successfully sent email for {aoi.stem} and {len(recent_aoi)} incidents."
                )
            except:
                logging.info(
                    f"Failed to send email for {aoi.stem} and {len(recent_aoi)} incidents."
                )

        # No incident(s)
        else:
            send_email(subject=f"No incidents for {aoi.stem}", body=aoi.stem, table_html=None, image_url=None)
            logging.info(f"No incidents for {aoi.stem}.")
            