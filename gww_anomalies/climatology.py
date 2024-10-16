"""functions for creating a reservoir climatology file."""

from __future__ import annotations

import logging
from datetime import datetime

import geopandas as gpd
from tqdm import tqdm

from gww_anomalies import CACHE_PATH
from gww_anomalies.gww_api import get_multi_reservoir_ts
from gww_anomalies.utils import get_reservoir_geometries

logger = logging.getLogger()
now = datetime.now()


def get_climatology(
    start: datetime = datetime(2000, 1, 1),
    end: datetime = now,
    reservoir_locations: str | None = None,
    *,
    update_locations: bool = False,
):
    if not reservoir_locations:
        reservoir_locations = CACHE_PATH / "reservoirs.gpkg"
    if not reservoir_locations.exists() or update_locations:
        get_reservoir_geometries(
            reservoir_locations=reservoir_locations,
        )
    reservoir_geoms = gpd.read_file(reservoir_locations)
    reservoir_ids = reservoir_geoms["feature_id"].to_list()
    logger.info("Retrieving reservoir timeseries from GWW API for creating reservoir climatologies")
    chunk_size = 10
    reservoir_ids = reservoir_ids[:20]  # TODO: remove for testing
    for i in tqdm(range(0, len(reservoir_ids), chunk_size)):
        chunk = reservoir_ids[i : i + chunk_size]
        data = get_multi_reservoir_ts(reservoir_ids=chunk, start=start, stop=end)
