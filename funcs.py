import requests
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

