import pandas as pd
import requests
from datetime import datetime
from gww_anomalies.funcs import filter_reservoirs
from gww_anomalies import CACHE_PATH
from gww_anomalies.gww_api import get_multi_reservoir_ts
from pathlib import Path
from google.cloud import storage
import geopandas as gpd
import logging


logger = logging.getLogger()




def get_climatology(
    min_area: float,
    max_area: float,
    start: datetime = datetime(200, 1, 1),
    end: datetime = datetime.now(),
    reservoir_locations: str | None = None,
):
    if not reservoir_locations:
        reservoir_locations = CACHE_PATH / "reservoirs.gpkg" 
    if not reservoir_locations.exists():
        get_reservoir_geometries(
            reservoir_locations=reservoir_locations,
        )
    reservoir_geoms = gpd.read_file(reservoir_locations)
    reservoir_geoms_sel = filter_reservoirs(
        reservoir_geoms, min_val=min_area, max_val=max_area
    )
    reservoir_ids = reservoir_geoms_sel["fid"].values
    percentage_left = len(reservoir_ids) / len(reservoir_geoms) * 100
    log_msg = "After filtering for size, {:1.2f} percent of reservoirs is left for analysis".format(
        percentage_left
    )
    logger.info(log_msg)
    logger.info("Retrieving reservoir timeseries from GWW API")
    chunk_size = 100
    for i in range(0, len(reservoir_ids), chunk_size):
        chunk = reservoir_ids[i:i + chunk_size]

    



def get_reservoir_geometries(
     reservoir_locations: str | Path
):
    storage_client = storage.Client()
    bucket = storage_client.bucket("global-water-watch")
    blob = bucket.blob("global-water-watch/shp/reservoirs-v1.0.gpkg")
    logger.info("Downloading reservoir locations from global-water-watch cloud bucket to cache")
    blob.download_to_filename(reservoir_locations)
