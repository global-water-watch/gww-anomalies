"""functions for creating a reservoir climatology file."""

from __future__ import annotations

import logging
from datetime import datetime

import geopandas as gpd

from gww_anomalies import CACHE_PATH
from gww_anomalies.gww_api import get_multi_reservoir_ts
from gww_anomalies.utils import filter_reservoirs, get_reservoir_geometries

logger = logging.getLogger()
now = datetime.now()


def get_climatology(
    min_area: float,
    max_area: float,
    start: datetime = datetime(200, 1, 1),
    end: datetime = now,
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
        reservoir_geoms,
        min_val=min_area,
        max_val=max_area,
    )
    reservoir_ids = reservoir_geoms_sel["fid"].to_numpy()
    percentage_left = len(reservoir_ids) / len(reservoir_geoms) * 100
    log_msg = f"After filtering for size, {percentage_left:1.2f} percent of reservoirs is left for analysis"
    logger.info(log_msg)
    logger.info("Retrieving reservoir timeseries from GWW API")
    chunk_size = 100
    reservoir_ids = reservoir_ids[:200]  # TODO remove for testing
    for i in range(0, len(reservoir_ids), chunk_size):
        chunk = reservoir_ids[i : i + chunk_size]
        data = get_multi_reservoir_ts(reservoir_ids=chunk, start=start, stop=end)
