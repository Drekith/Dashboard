from __future__ import annotations

import threading
from typing import Iterable, List

from dashboard.providers.base import DataProvider
from dashboard.state import VehicleState, VehicleUpdate


class DataPipeline:
    def __init__(self, providers: Iterable[DataProvider]):
        self.providers: List[DataProvider] = list(providers)
        self.state = VehicleState()
        self._lock = threading.Lock()

    def start(self) -> None:
        for provider in self.providers:
            provider.start()

    def stop(self) -> None:
        for provider in self.providers:
            provider.stop()

    def replace_providers(self, providers: Iterable[DataProvider]) -> None:
        self.stop()
        self.providers = list(providers)
        self.start()

    def apply_update(self, update: VehicleUpdate) -> None:
        with self._lock:
            self.state.apply_update(update)

    def snapshot(self) -> VehicleState:
        with self._lock:
            return VehicleState(**self.state.__dict__)
