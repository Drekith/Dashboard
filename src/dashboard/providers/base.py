import importlib.util
import platform
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

    def probe(self) -> bool:
        """Return whether the provider can run.

        Subclasses should override when a lightweight connectivity check is
        possible. The default implementation assumes success.
        """

        return True

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

    def _require_win32com(self) -> None:
        """Ensure win32com is available on Windows for usb2can backends.

        python-can's usb2can interface depends on the Windows COM bridge. Giving
        an explicit error message here helps users install ``pywin32`` when
        running on Windows.
        """

        if platform.system() != "Windows":
            return

        spec = importlib.util.find_spec("win32com.client")
        if spec is None:
            raise RuntimeError(
                "win32com.client is missing; install pywin32 to use the Waveshare USB-to-CAN adapter"
            )
