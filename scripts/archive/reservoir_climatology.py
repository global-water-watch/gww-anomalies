import os

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import ruptures as rpt
import tqdm
from gwwstorage import cloud
from scipy import stats


def change_detect(df, tolerance=0.7):
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
    algo = rpt.Dynp(model="l2").fit(df.area.values)
    change_loc = algo.predict(n_bkps=1)
    index = change_loc[0]
    m1 = df.iloc[:index].mean()
    m2 = df.iloc[index:].mean()
    if (m1 / m2).values[0] < tolerance:
        return change_loc
    return None


def plot_change_points(ts, ts_change_loc):
    f, ax = plt.subplots(1, 1, figsize=(16, 4))
    # ax = f.add_axes()
    ax.plot(ts)
    for x in ts_change_loc:
        ax.axvline(x, lw=2, color="red")
    return f


### FUNCTIONS HERE


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


def quantile_trans(ts, fit_params, p_zero, dist="norm"):
    """This function detrermines the normal quantile transform of a number of samples, based on
    a known (e.g. Gamma) distribution of the process (can in principle
    be extended to support grids instead of point values)
    Input:
        samples            : the samples from the process, for which standardized index is
                             computed
        fit_params         : the distribution parameters (need to be of expected size for given distribution)
        loc                : the location (mean) parameter of the distribution
        beta               : the scale parameter of the distribution
        prob_zero          : the probability of zero-rainfall
        dist:              : chosen distribution, compatible with scipy.stats
    Output:
        standardized       : Standardized values of the given samples
    """
    # compute probability of non-exceeding of given sample(s), given the predefined Gamma distribution
    samples = ts.values
    # find zero samples (only relevant for processes that are zero-bounded such as fluxes, e.g. precipitation)
    if p_zero > 0:
        ii = samples == 0
    # find missings in samples
    jj = np.isnan(samples)
    # get the requested distribution
    dist_func = getattr(stats, dist)
    # compute the cumulative distribution function quantile values using the fitted parameters
    cdf_samples = dist_func.cdf(samples, *fit_params)
    # correct for no rainfall probability
    cdf_samples = p_zero + (1 - p_zero) * cdf_samples
    if p_zero > 0:
        cdf_samples[ii] = p_zero
    cdf_samples[jj] = np.nan
    # compute inverse normal distribution with mu=0 and sigma=1, this yields the standardized values.
    # Basically this means looking up how many standard deviations the given quantile represents in
    # a normal distribution with mu=0. and sigma=1.
    standardized = stats.norm.ppf(cdf_samples)
    return standardized


def fit_and_transform(samples, dist="norm", include_zero=True):
    # The function below fits the samples to the requested distribution 'norm' or other from scipy.stats
    fit_params, p_zero = fit(samples, dist=dist, include_zero=include_zero)
    # Then the fitted parameters are used to estimate the standardized samples for each invidual month
    standardized_samples = quantile_trans(samples, fit_params, p_zero, dist=dist)
    # finally, the standardized samples are put into a pandas timeseries again, so that we can easily make time series plots
    # and do further analyses
    return pd.Series(standardized_samples, index=samples.index)


def compute_standard_index(ts, index="time.month", dist="norm", include_zero=True):
    """Compute standardised index. This is done on monthly time series by:
    - grouping the monthly data into monthly bins
    - for each month fit a distribution function (normal or other from scipy.stats)
    - estimate the probability of exceedance of each point in the time series using the 12 distributions
    - estimate the normal transform of each probability found using mapping to a standard normal distribution
    Input:
        ts: pandas Series object containing monthly data (e.g. monthly precipitation, precip-ref. evaporation)
        index='time.month': index to use for grouping
        dist='norm': distribution to use.
    """
    # first, we group all values per month. So we get a group of January rainfalls, February rainfalls, etc.
    ts_group = ts.groupby(ts.index.month)
    # for each group, the SPI values are computed and coerced into a new time series.
    standardized_index = ts_group.apply(fit_and_transform, dist=dist, include_zero=include_zero)
    return standardized_index


base_dir = r"c:\tmp\GWW-data"
key = "fid"
verbose = False
# verbose = True
bucket_loc = "reservoir-time-series-2022-Q3/time_series_area_monthly"

# start client with bucket
bucket = cloud.get_bucket()
reservoir_shp = os.path.join(base_dir, "shp", "reservoirs-locations-v1.0.shp")
dir_time_series = os.path.join(base_dir, "climatology_ts")
climatology = os.path.join(base_dir, "climatology")
fig_path = os.path.join(base_dir, "climatology_ts_figs")

if not os.path.isdir(dir_time_series):
    os.makedirs(dir_time_series)

if not os.path.isdir(climatology):
    os.makedirs(climatology)

if not os.path.isdir(fig_path):
    os.makedirs(fig_path)

# define start and end time for climatology
start_time = "2000-01-01"
end_time = "2020-12-31"
dist = "norm"
include_zero = False
min_sample_tolerance = 5  # minimum 5 years of data

# read geopackage in memory
print(f"Reading {reservoir_shp}")
gdf_res = gpd.read_file(reservoir_shp)

gdf_res = gdf_res.iloc[13000:]
if not (verbose):
    p = tqdm.tqdm(gdf_res["fid"])
else:
    p = gdf_res["fid"]
for reservoir in p:
    # reservoir with break on 2009: 91539
    # Mita hills: 87292
    # Roseires: 90393

    url = bucket_loc + f"/{reservoir:07d}.csv"
    blobs = bucket.list_blobs(prefix=url)
    # try:
    for blob in blobs:
        fn = os.path.join(dir_time_series, os.path.split(blob.name)[-1])
        fn_out = os.path.join(
            climatology,
            f"clim_{reservoir:07d}.csv",
        )
        if os.path.isfile(fn_out):
            continue
        if not os.path.isfile(fn):
            if verbose:
                print(f"Writing {blob.name} to {fn}")
            blob.download_to_filename(fn)
        elif verbose:
            print(f"Reading existing file {fn}")
        # read in memory
        df = pd.read_csv(fn, index_col="time", parse_dates=True)
        # read start / end time
        df = df[start_time:end_time]
        if len(df) < 100:
            # series too short, break off
            if verbose:
                print(f"series of reservoir {reservoir} too short, skipping")
            continue
        # change point detection, reduce series if necessary
        locs = change_detect(df, tolerance=0.7)

        if locs is not None:
            fn_jpg = os.path.join(fig_path, f"series_change_{reservoir:07d}.jpg")
            f = plot_change_points(df.area.values, locs)
            f.savefig(fn_jpg, bbox_inches="tight", dpi=72)
            plt.close("all")
            df = df.iloc[locs[0] :]

        df_g = df.groupby(df.index.month)
        min_samples = np.array([len(g) for n, g in df_g]).min()
        if min_samples < min_sample_tolerance:
            if verbose:
                print(
                    f"Minimum sample size per month should be {min_sample_tolerance}, but is {min_samples} skipping {reservoir}"
                )
            continue
        pars = df_g.apply(fit, dist=dist, include_zero=include_zero)

        # make a nice table
        pars_array = np.array([list(p[0]) for p in pars])
        pars_df = pd.DataFrame(data={"mean": pars_array[:, 0], "std": pars_array[:, 1]}, index=pars.index)
        if verbose:
            print(f"Storing derived climatology pars in {fn_out}")
        pars_df.to_csv(fn_out)


# upload to google
# blob = bucket.blob(f"climatology_2000_2020/{os.path.split(fn_out)[-1]}")
# blob.upload_from_filename(fn_out)

# join with all shapes

# print("do something")
# print(gdf_res.head())
