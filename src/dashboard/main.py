import os
import sys
from pathlib import Path

# Allow running this file directly (e.g., `python src/dashboard/main.py`) by
# ensuring the project root (containing the `dashboard` package) is on sys.path.
if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import importlib.util

from PySide6 import QtWidgets

from dashboard.providers.can_provider import CanProvider
from dashboard.providers.kline_provider import KLineProvider
from dashboard.providers.simulator import SimulatorProvider
from dashboard.services.data_pipeline import DataPipeline
from dashboard.ui.main_window import MainWindow
from dashboard.state import VehicleUpdate


def _auto_detect_kline_port(env_value: str) -> str:
    if env_value:
        return env_value

    spec = importlib.util.find_spec("serial")
    if spec is None:
        return ""

    from serial.tools import list_ports

    for port in list_ports.comports():
        description = port.description.upper()
        if "ELM" in description or "OBD" in description or "USB" in description:
            return port.device
    return ""


def _attempt_provider(build_fn, pipeline: DataPipeline, label: str):
    try:
        provider = build_fn()
    except Exception as exc:  # noqa: BLE001
        pipeline.apply_update(
            VehicleUpdate(ambient_assist_message=f"{label} init failed: {exc}")
        )
        return None

    if hasattr(provider, "probe") and not provider.probe():
        pipeline.apply_update(
            VehicleUpdate(ambient_assist_message=f"{label} not detected; using simulator")
        )
        return None
    return provider


def build_pipeline() -> DataPipeline:
    can_channel = os.getenv("CAN_CHANNEL", "")
    kline_port = _auto_detect_kline_port(os.getenv("KLINE_PORT", ""))
    can_bitrate = int(os.getenv("CAN_BITRATE", "500000"))
    kline_baud = int(os.getenv("KLINE_BAUD", "10400"))

    pipeline = DataPipeline([])

    providers = []
    if can_channel:
        can_provider = _attempt_provider(
            lambda: CanProvider(channel=can_channel, bitrate=can_bitrate, on_update=pipeline.apply_update),
            pipeline,
            "CAN",
        )
        if can_provider:
            providers.append(can_provider)
    if kline_port:
        kline_provider = _attempt_provider(
            lambda: KLineProvider(port=kline_port, baudrate=kline_baud, on_update=pipeline.apply_update),
            pipeline,
            "K-Line",
        )
        if kline_provider:
            providers.append(kline_provider)

    if not providers:
        providers.append(SimulatorProvider(on_update=pipeline.apply_update))
        pipeline.apply_update(
            VehicleUpdate(ambient_assist_message="No hardware detected; simulator active")
        )
    else:
        providers.append(SimulatorProvider(on_update=pipeline.apply_update, refresh_rate=1.0))

    pipeline.providers = providers
    return pipeline


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    pipeline = build_pipeline()
    window = MainWindow(pipeline)
    pipeline.start()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
