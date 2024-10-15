import os
import pandas as pd
import time
from tqdm import tqdm

from datetime import datetime
from dateutil.relativedelta import relativedelta







def patch_api_resource_watch(base_url, end_point, body={}):
    """
    Patch data set on API of resource watch.

    Check example code on resource watch repositories, e.g.

    https://github.com/resource-watch/nrt-scripts/blob/master/cli_035_surface_temp_analysis/contents/src/__init__.py

    """
    raise NotImplementedError



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


# anomaly computation
def anomaly(df, df_clim):
    """
    Returns
    -------

    df : DataFrame of dataset
        column: reservoir_id
        index: datetime of anomaly

    """
    # add common column for month
    df_clim["month"] = df_clim.index
    df['month'] = df.index.month
    df_anom = df.merge(df_clim, on='month', how='left')
    df_anom.index = df.index
    df_anom.index.name = "time"
    df_anom["anomaly"] = (df_anom["surface_area"] - df_anom["mean"]) / df_anom["std"]
    df_anom.drop(columns=["mean", "std"], inplace=True)
    return df_anom


def anomalies_all(dfs, dfs_clim):
    # compute all anomalies for all reservoirs
    for k in dfs:
        dfs[k] = anomaly(dfs[k], dfs_clim[k])
    return dfs


def parse_df_to_body():
    """
    Parse DataFrame with reservoir anomalies to a body that can be submitted to an API (e.g. ResourceWatch)

    Returns
    -------



    """
    raise NotImplementedError