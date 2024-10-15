"""A Python package for retrieving Global Water Watch reservoir anomalies."""

from platformdirs import user_cache_dir
from pathlib import Path

CACHE_PATH: Path = Path(user_cache_dir("gww-anomalies", ensure_exists=True))

__version__ = "0.0.1"
