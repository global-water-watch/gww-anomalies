"""Lightweight CLI for calculating reservoir anomalies."""

from __future__ import annotations

import argparse
from pathlib import Path

from gww_anomalies.main import run

parser = argparse.ArgumentParser()
parser.add_argument("output_dir", help="Output directory to write the reservoir anomalies file to")
parser.add_argument(
    "-r",
    "--reservoir_ids_file",
    help="Text file containing reservoir fids seperated by commas and on one line",
)
parser.add_argument("-v", "--as-vector", help="Write anomalies file to a vector format")  # TODO: implement this


def _parse_reservoir_ids_file(fp: Path | str) -> list:
    with Path(fp).open("r") as f:
        ids = f.read()
    id_list = ids.split(",")

    try:
        fid_list = [int(x) for x in id_list]
    except ValueError as err:
        err_msg = "Reservoir feature ids must be integers"
        raise ValueError(err_msg) from err
    return fid_list


if __name__ == "__main__":
    args = parser.parse_args()
    fid_list = _parse_reservoir_ids_file(fp=args.reservoir_ids_file) if args.reservoir_ids_file else None
    run(output_dir=args.output_dir, reservoir_list=fid_list)
