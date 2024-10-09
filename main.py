import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import os

from datetime import datetime
from tqdm import tqdm

import funcs

MIN_VAL = 5e6 # 5 km2
# MIN_VAL = 1e8
MAX_VAL = 5e8 # 500 km2
SHAPEFILE = r"p:\11207650-esa-surface-to-storage\shp\reservoirs-locations-v1.0.shp"
CLIM_PATH = r"p:\11207650-esa-surface-to-storage\climatology\climatology"
CLIM_FMT = "clim_{:07d}.csv"


def main():
    shapefile = SHAPEFILE
    gdf = gpd.read_file(shapefile)
    print(f"Shapefile {shapefile} read in memory")
    gdf_sel = funcs.filter_reservoirs(gdf, min_val=MIN_VAL, max_val=MAX_VAL)

    # get the reservoir ids from the shapefile
    reservoir_ids = gdf_sel["fid"].values

    percentage_left = len(reservoir_ids) / len(gdf) * 100
    print("After filtering for size, {:1.2f} percent of reservoirs is left for analysis".format(percentage_left))

    # TODO: remove, for testing we only extract 20
    reservoir_ids = reservoir_ids[:200]

    # filter for available climatology
    res_ids = []
    for r in reservoir_ids:
        if os.path.isfile(os.path.join(CLIM_PATH, CLIM_FMT.format(r))):
            res_ids.append(r)
    percentage_left = len(res_ids) / len(gdf) * 100
    print(
        "After filtering for size and available climatology data, {:1.2f} percent of reservoirs is left for analysis".format(
            percentage_left))
    # read all climatologies
    dfs_clim = {
        res_id:funcs.read_climatology(
            path=CLIM_PATH,
            fmt=CLIM_FMT,
            reservoir_id=res_id
        ) for res_id in tqdm(res_ids)
    }

    # read reservoir time series data for the past month
    ts = funcs.get_reservoirs_per_interval(
        res_ids,
        curdate=datetime.utcnow(),
        interval=10,
        max_nr=100
    )
    # convert raw bodies into dataframes for easier manipulation
    dfs = funcs.bodies_to_df(ts)
    # aggregate to monthlies using resampling
    dfs_month = {k: v.resample("M").mean() for k, v in dfs.items()}

    # ensure the monthlies and climatology have the same order, use int as keys and missing months (no satellite data in month) are removed
    dfs_month = {i: dfs_month[str(i)] for i in dfs_clim.keys() if str(i) in dfs_month}
    dfs_clim = {i: dfs_clim[i] for i in dfs_clim.keys() if i in dfs_month}

    dfs_anom = funcs.anomalies_all(dfs_month, dfs_clim=dfs_clim)

    # TODO: convert plot stuff below into a function
    # select locs for plotting
    gdf.index = gdf.fid
    gdf_sel = gdf.loc[list(dfs_month.keys())]
    anoms = np.array([float(dfs_anom[k]["anomaly"].values) for k in dfs_anom])
    areas = np.array([float(dfs_anom[k]["surface_area"].values) for k in dfs_anom])
    x = np.float64(gdf_sel.geometry.x)
    y = np.float64(gdf_sel.geometry.y)
    ax = plt.axes()
    bounds = np.linspace(-3., 3., 9)
    norm = matplotlib.colors.BoundaryNorm(boundaries=bounds, ncolors=256)
    ax.scatter(
        x,
        y,
        s=areas / 5e4,
        c=anoms,
        alpha=0.8,
        norm=norm,
        cmap="RdYlBu",
        edgecolor="#555555",
        linewidth=1,
    )
    # gdf_sel.plot(column="anomaly", vmin=-2, vmax=2)
    plt.savefig("test.jpg", bbox_inches="tight", dpi=200)

    # TODO: figure out in what form/format data should be output,

    # TODO: figure out if a api request can be used to push results to dedicated end point (end point to be delivered by WRI).
    return dfs_anom

if __name__ == "__main__":
    main()