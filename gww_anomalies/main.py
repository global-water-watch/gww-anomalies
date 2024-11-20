"""Calculate reservoir anomalies."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from tqdm import tqdm

from gww_anomalies.gww_api import get_reservoir_ts
from gww_anomalies.utils import get_month_interval

if TYPE_CHECKING:
    from datetime import datetime
logger = logging.getLogger(__name__)


def run(
    output_dir: str | Path,
    reservoir_list: list[int] | None = None,
    month: str | None = None
) -> Path:
    """Calculate anomalies for given list of reservoir ids and writes to a CSV or vector file.

    If no reservoir ids are supplied, anomalies are calculated for all the reservoirs present in the climatologies file.

    Parameters
    ----------
    output_dir : str | Path
        Directory to write the anomaly dataset to.
    reservoir_list : list[int] | None, optional
        list of reservoir ids, by default None

    """
    data_dir = Path(__file__).absolute().parent.parent / "data"
    climatology_file = data_dir / "climatologies.parquet"
    climatologies = pd.read_parquet(climatology_file)
    if not reservoir_list:
        logger.info("No list of reservoirs given, calculating anomalies for all reservoirs that have climatology.")
        reservoir_list = climatologies["fid"].to_list()

    if month:
        month = datetime.strptime(month, format="dd-mm-YYYY")
    first_of_last_month, first_of_month = get_month_interval(month)
    anomaly_df = calculate_anomalies( 
        climatologies=climatologies,
        fids=reservoir_list,
        start=first_of_last_month,
        stop=first_of_month,
    )
    output_path = Path(output_dir) / f"anomalies_{first_of_last_month.month}_{first_of_last_month.year}.csv"
    logging.info("Writing anomaly dataset to %s", output_path)
    anomaly_df.to_csv(output_path)
    return output_path


def calculate_anomalies(climatologies: pd.DataFrame, fids: list[int], start: datetime, stop: datetime) -> pd.DataFrame:
    """Calculate reservoir anomalies based on reservoir climatology.

    Parameters
    ----------
    climatologies : pd.DataFrame
        dataframe containing climatologies of reservoirs
    fids : list[int]
        list of feature ids for reservoirs
    start : datetime
        start date to calculate anomalies for
    stop : datetime
        end date to calculate anomalies

    Returns
    -------
    pd.DataFrame
        dataframe containing the anomalies and surface water area for the given time period.

    """
    month = start.month
    reservoir_surface_areas = []
    logging.info(
        "Retrieving surface water area for %s reservoirs for the period of %s - %s",
        len(fids),
        start,
        stop,
    )
    for fid in tqdm(fids):
        if fid not in climatologies["fid"]:
            warning_msg = f"reservoir {fid} not found in climatologies dataset!"
            logger.warning(warning_msg)
            continue
        reservoir_ts = get_reservoir_ts(
            reservoir_id=str(fid),
            start=start,
            stop=stop,
            var_name="surface_water_area",
        )
        if not reservoir_ts:
            continue
        monthly_surface_area = sum([x["value"] for x in reservoir_ts]) / len(reservoir_ts)
        reservoir_surface_areas.append({"fid": fid, "monthly_surface_area": monthly_surface_area})
    reservoir_surface_areas_df = pd.DataFrame(reservoir_surface_areas)
    anomalies_df = reservoir_surface_areas_df.join(climatologies, on="fid", how="inner", rsuffix="r")
    anomalies_df["anomaly"] = (anomalies_df["monthly_surface_area"] - anomalies_df[f"mean_{month}"]) / anomalies_df[
        f"std_{month}"
    ]
    return anomalies_df[["fid", "anomaly", "monthly_surface_area"]]
