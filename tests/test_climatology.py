from datetime import datetime

from gww_anomalies.climatology import get_climatology


def test_get_climatology():
    start_date = datetime(2000, 1, 1)
    end_date = datetime(2024, 10, 1)
    get_climatology(start=start_date, end=end_date, update_locations=True)
