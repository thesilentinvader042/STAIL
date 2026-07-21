"""
Loads rubric.yaml once at import time.
All scoring modules import `cfg` from here.
"""

from __future__ import annotations
import os
from pathlib import Path
from functools import lru_cache
import yaml


@lru_cache(maxsize=1)
def load_rubric() -> dict:
    path = Path(__file__).parent / "rubric.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


# Convenience accessor — `from config.loader import cfg`
cfg = load_rubric()