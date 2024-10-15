from datetime import datetime

from gww_anomalies.climatology import get_climatology


def test_get_climatology():
    start_date = datetime(2000, 1, 1)
    end_date = datetime(2024, 10, 1)
    get_climatology(min_area=5e6, max_area=5e8, start=start_date, end=end_date)
