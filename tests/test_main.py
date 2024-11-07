import logging

import pandas as pd

from gww_anomalies.main import run


def test_run(caplog, tmp_path, mocker):
    caplog.set_level(logging.INFO)
    output_path = run(output_dir=tmp_path, reservoir_list=[14299])
    assert f"Writing anomaly dataset to {output_path}" in caplog.text
    assert output_path.exists()
    mock_anomalies = mocker.patch("gww_anomalies.main.calculate_anomalies")
    mock_anomalies.return_value = pd.DataFrame()
    output_path = run(output_dir=tmp_path)
    assert "No list of reservoirs given, calculating anomalies for all reservoirs that have climatology." in caplog.text
