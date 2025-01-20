"""Calculate reservoir anomalies."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import pandas as pd
from tqdm import tqdm

from gww_anomalies.gww_api import get_reservoir_ts
from gww_anomalies.utils import get_month_interval

logger = logging.getLogger(__name__)


def run(
    output_dir: str | Path,
    data_dir: Path,
    reservoir_list: list[int] | None = None,
    month: str | None = None,
    as_vector: bool | None = None,
) -> Path:
    """Calculate anomalies for given list of reservoir ids and writes to a CSV or vector file.

    If no reservoir ids are supplied, anomalies are calculated for all the reservoirs present in the climatologies file.

    Parameters
    ----------
    output_dir : str | Path
        Directory to write the anomaly dataset to.
    data_dir: Path
        Directory containing the data needed for calculating
    reservoir_list : list[int] | None, optional
        list of reservoir ids, by default None
    month : str | None, optional
        date string in format 'dd-mm-YYYY'
    as_vector: bool | None, optional
        return the anomalies dataframe as a GeoJSON file

    """
    climatology_file = data_dir / "climatologies.parquet"
    climatologies = pd.read_parquet(climatology_file)
    if not reservoir_list:
        logger.info("No list of reservoirs given, calculating anomalies for all reservoirs that have climatology.")
        reservoir_list = climatologies["fid"].to_list()

    if month:
        month = datetime.strptime(month, format="dd-mm-YYYY")  # noqa: DTZ007
    first_of_last_month, first_of_month = get_month_interval(month)
    anomaly_df = calculate_anomalies(
        climatologies=climatologies,
        fids=reservoir_list,
        start=first_of_last_month,
        stop=first_of_month,
    )
    if not anomaly_df.empty:
        output_path = Path(output_dir) / f"anomalies_{first_of_last_month.month}_{first_of_last_month.year}"
        if as_vector:
            output_path = _to_vector(anomalies_df=anomaly_df, output_path=output_path, data_dir=data_dir)
        else:
            output_path = output_path.with_suffix(".csv")
            anomaly_df.to_csv(output_path)

        logging.info("Writing anomaly dataset to %s", output_path)
        return output_path
    logger.warning("No anomalies calculated for the given reservoirs")
    return None


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
        if fid not in climatologies["fid"].to_numpy():
            warning_msg = f"reservoir {fid} not found in climatologies dataset!"
            logger.warning(warning_msg)
            continue
        reservoir_ts = get_reservoir_ts(
            reservoir_id=fid,
            start=start,
            stop=stop,
            var_name="surface_water_area",
        )
        if not reservoir_ts:
            logging.info("No reservoir timeseries found for resevoir with id %s.", fid)
            continue
        monthly_surface_area = sum([x["value"] for x in reservoir_ts]) / len(reservoir_ts)
        reservoir_surface_areas.append({"fid": fid, "monthly_surface_area": monthly_surface_area})
    reservoir_surface_areas_df = pd.DataFrame(reservoir_surface_areas)
    if reservoir_surface_areas_df.empty:
        logging.warning("No surface water area found for all reservoirs of interest.")
        return None
    anomalies_df = reservoir_surface_areas_df.merge(climatologies, on="fid", how="inner")
    anomalies_df["anomaly"] = (anomalies_df["monthly_surface_area"] - anomalies_df[f"mean_{month}"]) / anomalies_df[
        f"std_{month}"
    ]
    return anomalies_df[["fid", "anomaly", "monthly_surface_area"]]


def _to_vector(anomalies_df: pd.DataFrame, output_path: Path, data_dir: Path) -> str:
    reservoir_locations_path = data_dir / "reservoirs-locations-v1.0.gpkg"
    reservoir_locations = gpd.read_file(reservoir_locations_path)
    reservoir_locations = reservoir_locations.rename(columns={"feature_id": "fid"})
    anomalies_gdf = reservoir_locations.merge(anomalies_df, on="fid", how="inner")
    output_path = output_path.with_suffix(".geojson")
    anomalies_gdf.to_file(output_path)
    return output_path
