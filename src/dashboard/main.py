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

from dashboard.config import ProviderConfig, auto_detect_kline_port
from dashboard.providers.bcm_can_provider import BcmCanProvider
from dashboard.providers.can_provider import CanProvider
from dashboard.providers.kline_provider import KLineProvider
from dashboard.providers.simulator import SimulatorProvider
from dashboard.services.data_pipeline import DataPipeline
from dashboard.state import VehicleUpdate
from dashboard.ui.main_window import MainWindow


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
def build_providers(config: ProviderConfig, pipeline: DataPipeline):
    providers = []
    if config.can_channel:
        can_provider = _attempt_provider(
            lambda: CanProvider(
                channel=config.can_channel,
                bitrate=config.can_bitrate,
                on_update=pipeline.apply_update,
            ),
            pipeline,
            "CAN",
        )
        if can_provider:
            providers.append(can_provider)
    if config.bcm_can_channel:
        bcm_provider = _attempt_provider(
            lambda: BcmCanProvider(
                channel=config.bcm_can_channel,
                bitrate=config.bcm_can_bitrate,
                on_update=pipeline.apply_update,
            ),
            pipeline,
            "BCM CAN",
        )
        if bcm_provider:
            providers.append(bcm_provider)
    if config.kline_port:
        kline_provider = _attempt_provider(
            lambda: KLineProvider(
                port=config.kline_port,
                baudrate=config.kline_baud,
                on_update=pipeline.apply_update,
            ),
            pipeline,
            "K-Line",
        )
        if kline_provider:
            providers.append(kline_provider)

    if not providers:
        if config.enable_simulator:
            providers.append(SimulatorProvider(on_update=pipeline.apply_update))
            pipeline.apply_update(
                VehicleUpdate(
                    ambient_assist_message="No hardware detected; simulator active"
                )
            )
        else:
            pipeline.apply_update(
                VehicleUpdate(
                    ambient_assist_message=(
                        "No providers active; enable simulator or configure ports"
                    )
                )
            )
    elif config.enable_simulator:
        providers.append(SimulatorProvider(on_update=pipeline.apply_update, refresh_rate=1.0))
    return providers


def build_pipeline(config: ProviderConfig | None = None) -> tuple[DataPipeline, ProviderConfig]:
    config = config or ProviderConfig.from_env()
    pipeline = DataPipeline([])
    pipeline.providers = build_providers(config, pipeline)
    return pipeline, config


def reconfigure_pipeline(pipeline: DataPipeline, config: ProviderConfig) -> None:
    pipeline.replace_providers(build_providers(config, pipeline))


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    pipeline, config = build_pipeline()
    window = MainWindow(
        pipeline,
        config=config,
        reconfigure_callback=lambda cfg: reconfigure_pipeline(pipeline, cfg),
        auto_detect_kline=auto_detect_kline_port,
    )
    pipeline.start()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
