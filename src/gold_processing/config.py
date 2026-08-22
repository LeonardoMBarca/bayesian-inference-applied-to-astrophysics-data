"""Configuration loader for GOLD processing scripts."""

from __future__ import annotations

import importlib
from types import ModuleType


def load_default_config() -> ModuleType:
    return importlib.import_module("gold_data_config")
