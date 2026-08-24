"""Block standard Python socket networking in clean-rebuild subprocesses."""

from __future__ import annotations

import os
import socket
from pathlib import Path
from typing import NoReturn

MESSAGE = "network disabled by the clean-rebuild Python socket guard"
LOG_ENVIRONMENT_VARIABLE = "CLEAN_REBUILD_NETWORK_GUARD_LOG"


def _blocked(api_name: str) -> NoReturn:
    log_path = os.environ.get(LOG_ENVIRONMENT_VARIABLE)
    if log_path:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"{api_name}\n")
    raise OSError(f"{MESSAGE}: {api_name}")


def _blocked_connect(self: socket.socket, address: object) -> NoReturn:
    del self, address
    _blocked("socket.socket.connect")


def _blocked_connect_ex(self: socket.socket, address: object) -> NoReturn:
    del self, address
    _blocked("socket.socket.connect_ex")


def _blocked_create_connection(*args: object, **kwargs: object) -> NoReturn:
    del args, kwargs
    _blocked("socket.create_connection")


def _blocked_getaddrinfo(*args: object, **kwargs: object) -> NoReturn:
    del args, kwargs
    _blocked("socket.getaddrinfo")


socket.socket.connect = _blocked_connect
socket.socket.connect_ex = _blocked_connect_ex
socket.create_connection = _blocked_create_connection
socket.getaddrinfo = _blocked_getaddrinfo
