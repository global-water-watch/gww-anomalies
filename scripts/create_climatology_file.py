import requests
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import ruptures as rpt
from tqdm import tqdm
from scipy import stats


from gww_anomalies.utils import download_reservoir_geometries
from gww_anomalies.gww_api import get_reservoir_ts

START_DATE: datetime = datetime(2000,1,1)
END_DATE: datetime = datetime.now() # To get the most recent surface areas
DIST: str = "norm"
MIN_SAMPLE_SIZE: int = 5 # minimum of 5 years of data
INCLUDE_ZERO: bool = False

def change_detect(df, tolerance=0.7, value: str = "value"):
    """Change detection for reservoir behavior. Detected changes are evaluated by comparing the mean of the first
    against the mean of the second period. If they significantly deviate, then the change is considered valid, other
    wise not.

    Parameters
    ----------
    series : array-like
        list, array or other with values to evaluate changes on
    tolerance : float
        If mean of first period divided by mean of second period is smaller than tolerance, the change is considered
        valid.

    Returns
    -------
    change point as index (or None if not reaching the tolerance)

    """
    algo = rpt.Dynp(model="l2").fit(df[value].values)
    change_loc = algo.predict(n_bkps=1)
    index = change_loc[0]
    m1 = df.iloc[:index].mean()
    m2 = df.iloc[index:].mean()
    if (m1 / m2).values[0] < tolerance:
        return change_loc
    return None

def fit(ts, dist="norm", include_zero=False):
    """This function fits a distribution (e.g. default gamma, but can be altered to
    genextreme, normal, or other supported by scipy.stats) from a number of samples. It can (should) be tested
    whether the process fits chosen distribution, e.g. with a goodness of fit or Q-Q plots.
    Input:
        samples            : the samples from the process, to be described by
                             the Gamma distribution
        dist:              : chosen distribution, compatible with scipy.stats
        include_zero       : Default: True, decide if probability of zero values occurring should be included
                             explicitly
    Output:
        fit_params         : tuple with fit parameters of chosen distribution such as shape, location, scale
        prob_zero          : the probability of zero occurring (if relevant)

    """
    samples = ts.values.flatten()  # flatten the matrix to a one-dimensional array
    if include_zero:
        # compute probability of zero (only relevant for things like rainfall)
        prob_zero = float(sum(samples == 0)) / len(samples)
    else:
        prob_zero = 0.0
    # find the amount of samples
    n = len(samples)
    # select the gamma distribution function to work with
    dist_func = getattr(stats, dist)
    # fit parameters of chosen distribution function, only through non-zero samples
    if include_zero:
        fit_params = dist_func.fit(samples[(samples != 0) & np.isfinite(samples)])
    else:
        fit_params = dist_func.fit(samples[np.isfinite(samples)])
    # following is returned from the function
    return fit_params, prob_zero






def main():
    reservoir_locations_fp = Path("data/reservoirs-locations-v1.0.gpkg")
    if not reservoir_locations_fp.exists():
        download_reservoir_geometries(reservoir_locations_fp)
    reservoir_locations = gpd.read_file(reservoir_locations_fp)
    reservoir_locations = reservoir_locations.iloc[13000:] # first 13000 reservoirs are too small
    
    print(f"Retrieving surface water area timeseries for {len(reservoir_locations)} reservoirs")
    climatologies = []
    for fid in tqdm(reservoir_locations["feature_id"]):
        reservoir_ts = get_reservoir_ts(reservoir_id=fid, start=START_DATE, stop=END_DATE, var_name="surface_water_area_monthly")
        if len(reservoir_ts) < 100: # skip reservoirs that have less than 100 records
            continue
        df = pd.DataFrame(reservoir_ts)
        df["t"] = pd.to_datetime(df["t"], format="mixed")
        df.set_index("t", inplace=True)
        df.drop(columns=["name", "unit"], inplace=True) # Drop unnecessary data
        locs = change_detect(df, tolerance=0.7, value="value")
        if locs:
            df = df.iloc[locs[0]:]
        df_g = df.groupby(df.index.month)
        min_samples = np.array([len(g) for n, g in df_g]).min()
        if min_samples < MIN_SAMPLE_SIZE:
            continue # Dont calculate the 
        fit_params = df_g.apply(fit, dist=DIST, include_zero=INCLUDE_ZERO)
        params_array = np.array([list(p[0]) for p in fit_params])
        
        climatology = {"fid": fid}
        for x in range(12):
            climatology.update({f"mean_{x+1}": params_array[x][0]})
            climatology.update({f"std_{x+1}": params_array[x][1]})

        climatologies.append(climatology)
    climatology_df = pd.DataFrame(climatologies)
    climatology_df.to_parquet("data/climatologies.parquet")

            







    
        



if __name__ == "__main__":
    main()
