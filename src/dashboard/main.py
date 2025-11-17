import os
import sys

from PySide6 import QtWidgets

from dashboard.providers.can_provider import CanProvider
from dashboard.providers.kline_provider import KLineProvider
from dashboard.providers.simulator import SimulatorProvider
from dashboard.services.data_pipeline import DataPipeline
from dashboard.ui.main_window import MainWindow


def build_pipeline() -> DataPipeline:
    can_channel = os.getenv("CAN_CHANNEL", "")
    kline_port = os.getenv("KLINE_PORT", "")
    can_bitrate = int(os.getenv("CAN_BITRATE", "500000"))
    kline_baud = int(os.getenv("KLINE_BAUD", "10400"))

    pipeline = DataPipeline([])

    providers = []
    if can_channel:
        can_provider = CanProvider(channel=can_channel, bitrate=can_bitrate, on_update=pipeline.apply_update)
        providers.append(can_provider)
    if kline_port:
        kline_provider = KLineProvider(port=kline_port, baudrate=kline_baud, on_update=pipeline.apply_update)
        providers.append(kline_provider)

    if not providers:
        providers.append(SimulatorProvider(on_update=pipeline.apply_update))
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
