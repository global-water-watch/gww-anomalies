"""Functions for interacting with the GWW API."""

from __future__ import annotations

import logging
import time
from datetime import datetime

import requests
import tqdm

from gww_anomalies.utils import get_month_interval

base_url = "https://api.globalwaterwatch.earth"


# base functions for API calls such as retrieval of time series
def get_reservoir_ts(reservoir_id: str, start: datetime, stop: datetime) -> dict:
    """Get time series data for reservoir with given ID."""
    url = f"{base_url}/reservoir/{reservoir_id}/ts"
    params = {"start": start.strftime("%Y-%m-%dT%H:%M:%S"), "stop": stop.strftime("%Y-%m-%dT%H:%M:%S")}
    return requests.get(url, params=params).json()


def get_multi_reservoir_ts(
    reservoir_ids: list[str],
    start: datetime,
    stop: datetime,
    variable: str = "surface_water_area",
) -> dict:
    """Get time series data for multiple reservoirs.

    reservoir_ids : int, list[int]
        At least one id of reservoir(s)
    start : datetime
        start date time of the retrieval
    stop : datetime
        end date time of the retrieval
    variable : str, optional
        variable to retrieve from API (default: "surface_water_area")

    """
    url = f"{base_url}/ts"
    params = {
        "variable_name": variable,
        "start": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "stop": stop.strftime("%Y-%m-%dT%H:%M:%S"),
        "reservoir_ids": reservoir_ids,
        "agg_period": "monthly",
    }
    return requests.get(url, params=params)


def get_reservoirs_per_interval(res_ids, curdate=datetime.utcnow(), interval=10, max_nr=None):
    start, stop = get_month_interval()
    # count the time to read data
    t1 = time.time()

    ts = {}
    if max_nr is None:
        ns = range(0, int(len(res_ids)), interval)
    else:
        # limit to amount of available reservoirs
        max_nr = int(min(len(res_ids), max_nr))
        ns = range(0, max_nr, interval)
    log_msg = f"Reading {max_nr} reservoirs for datetime {start} until {stop} in batches of {interval}"
    logging.info(log_msg)
    for n in tqdm(ns):
        r = get_multi_reservoir_ts(res_ids[n : n + interval], start=start, stop=stop)
        data = r.json()
        if data["source_data"] is None:
            logging.warning("Warning, this interval contained no source data")
        else:
            ts.update(data["source_data"])
    t2 = time.time()

    log_msg = f"Reading month data for {len(res_ids[:interval])} reservoirs took {t2 - t1} seconds."
    logging.info(log_msg)
    return ts
