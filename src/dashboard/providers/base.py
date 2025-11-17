import threading
from abc import ABC, abstractmethod
from typing import Callable

from dashboard.state import VehicleUpdate

UpdateCallback = Callable[[VehicleUpdate], None]


class DataProvider(ABC):
    """Abstract provider that feeds updates into the UI.

    Providers should run in their own threads to avoid blocking the event loop.
    """

    def __init__(self, on_update: UpdateCallback):
        self.on_update = on_update
        self.thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    @abstractmethod
    def run(self) -> None:
        ...

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self._stop_event.clear()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self.thread:
            self.thread.join(timeout=1)

    def should_stop(self) -> bool:
        return self._stop_event.is_set()
