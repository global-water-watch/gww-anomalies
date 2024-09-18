import os
import pandas as pd
import requests
import time
import tqdm

from datetime import datetime
from dateutil.relativedelta import relativedelta

base_url = "https://api.globalwaterwatch.earth"


# base functions for retrieval of time series
def get_reservoir_ts(reservoir_id, start, stop):
    """
    Get time series data for reservoir with given ID
    """
    url = f"{base_url}/reservoir/{reservoir_id}/ts"
    params = {
        "start": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "stop": stop.strftime("%Y-%m-%dT%H:%M:%S")
    }
    return requests.get(url, params=params)


def get_multi_reservoir_ts(reservoir_ids, start, stop, variable="surface_water_area"):
    """
    Get time series data for multiple reservoirs.

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
        "agg_period": "monthly"
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
    print(f"Reading {max_nr} reservoirs for datetime {start} until {stop} in batches of {interval}")
    for n in tqdm(ns):
        r = get_multi_reservoir_ts(res_ids[n:n+interval], start=start, stop=stop)
        data = r.json()
        if data["source_data"] is None:
            print("Warning, this interval contained no source data")
        else:
            ts.update(data["source_data"])
    t2 = time.time()

    ts

    print(f"Reading month data for {len(res_ids[:interval])} reservoirs took {t2 - t1} seconds.")
    return ts



def get_month_interval(
        curdate=datetime.utcnow()
):
    """
    Get the last month's start and end date.

    curdate : datetime, optional
        current datetime (default: now!)
    """
    first_of_month = datetime(curdate.year, curdate.month, 1, 0, 0)
    month = relativedelta(months=1)
    first_of_last_month = first_of_month - month
    return first_of_last_month, first_of_month


def read_climatology(path, fmt, reservoir_id):
    fn = os.path.join(path, fmt.format(reservoir_id))
    df = pd.read_csv(fn, index_col="time")
    return df


# retrieval of a limited set of reservoirs from the full set based on minimum / maximum value
def filter_reservoirs(gdf, min_val, max_val, field="mean"):
    """
    Filter reservoirs from a GeoDataFrame based on values in a provided field
    gdf : gpd.GeoDataFrame
    min_val : float
        minimum value in `area_field`
    max_val : float
        maximum value in `area_field`
    field : str, optional
        field name in `gdf` to filter on (default: "mean")

    """
    gdf_sel = gdf[gdf[field] < max_val]
    gdf_sel = gdf_sel[gdf_sel[field] > min_val]
    return gdf_sel


def bodies_to_df(bodies):
    """
    Restructure sets of raw time series per reservoir (dict) to dict of pd.DataFrame

    Example input:
    ```
    {
        "00001": [
            {
                "t": "2024-09-01T00:00:00",
                "value": "12345000"
            },
            {
                "t": "2024-09-07T00:00:00",
                "value": "23456000"
            },
            ...
        ],
        "00002": [
            ...
        ]
    }
    ```

    Example output

    {
        "00001': surface_area
            2024-09-01  12345000
            2024-09-07  23456000,
        "00002": surface_area
            ...
    }


    """
    dfs = {}
    for k, data in bodies.items():
        index = pd.DatetimeIndex([v["t"] for v in data])
        vals = [v["value"] for v in data]
        dfs.update({k: pd.DataFrame({"surface_area": vals}, index=index)})
    return dfs
