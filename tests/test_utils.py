from pathlib import Path

from gww_anomalies.utils import _parse_reservoir_ids_file


def test_parse_reservoir_ids_file(tmp_path: Path):
    test_reservoir_ids = "90249, 38599"

    test_file = tmp_path / "test.txt"
    with test_file.open("w") as f:
        f.write(test_reservoir_ids)
    fid_list = _parse_reservoir_ids_file(test_file)
    assert fid_list[0] == "90249"
    assert fid_list[1] == "38599"

