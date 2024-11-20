"""Lightweight CLI for calculating reservoir anomalies."""

from __future__ import annotations

import argparse

from gww_anomalies.main import run
from gww_anomalies.utils import _parse_reservoir_ids_file

parser = argparse.ArgumentParser()
parser.add_argument("output_dir", help="Output directory to write the reservoir anomalies file to")
parser.add_argument(
    "-r",
    "--reservoir_ids_file",
    help="Text file containing reservoir fids seperated by commas and on one line",
)
parser.add_argument("-m", "--month", help="Calculate the anomalies by a given month in '01-mm-YYYY' format. By default the latest month is used.")
parser.add_argument("-v", "--as-vector", help="Write anomalies file to a vector format")  # TODO: implement this



if __name__ == "__main__":
    args = parser.parse_args()
    fid_list = _parse_reservoir_ids_file(fp=args.reservoir_ids_file) if args.reservoir_ids_file else None
    month = args.month
    run(output_dir=args.output_dir, reservoir_list=fid_list)
