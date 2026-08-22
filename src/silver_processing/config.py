"""Configuration loader for SILVER processing scripts."""

from __future__ import annotations

import importlib
from types import ModuleType


def load_default_config() -> ModuleType:
    """Load the repository-local SILVER configuration module."""

    return importlib.import_module("silver_data_config")
