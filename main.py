import geopandas as gpd
import os
import pandas as pd
from tqdm import tqdm

import funcs

MIN_VAL = 5e6 # 5 km2
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

    # filter for available climatology
    res_ids = []
    for r in reservoir_ids:
        if os.path.isfile(os.path.join(CLIM_PATH, CLIM_FMT.format(r))):
            res_ids.append(r)
    percentage_left = len(res_ids) / len(gdf) * 100
    print(
        "After filtering for size and available climatology data, {:1.2f} percent of reservoirs is left for analysis".format(
            percentage_left))
