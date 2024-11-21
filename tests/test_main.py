import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from gww_anomalies.main import calculate_anomalies, run
from gww_anomalies.utils import get_month_interval


def test_run(caplog, tmp_path, mocker):
    caplog.set_level(logging.INFO)
    output_path = run(output_dir=tmp_path, reservoir_list=[14299])
    assert f"Writing anomaly dataset to {output_path}" in caplog.text
    assert output_path.exists()
    mock_anomalies = mocker.patch("gww_anomalies.main.calculate_anomalies")
    mock_anomalies.return_value = pd.DataFrame()
    output_path = run(output_dir=tmp_path)
    assert "No list of reservoirs given, calculating anomalies for all reservoirs that have climatology." in caplog.text


def test_calculate_anomalies():
    test_data = Path(__file__).parent.parent / "data/climatologies.parquet"
    if not test_data.exists():
        pytest.skip("No data to test calculate_anomalies function")

    climatologies_df = pd.read_parquet(test_data)
    fid_list = [90249, 91611]
    start, stop = get_month_interval(date= datetime(2020,1,1))
    anomalies = calculate_anomalies(climatologies_df, fid_list, start, stop)
    assert isinstance(anomalies, pd.DataFrame)
    assert len(anomalies) == 2



