import importlib.util
import time
from typing import Any

from dashboard.providers.base import DataProvider
from dashboard.state import IndicatorState, VehicleUpdate


class CanProvider(DataProvider):
    """Reads BCM data from a Waveshare USB-to-CAN-A using python-can."""

    def __init__(self, channel: str, bitrate: int, on_update):
        super().__init__(on_update)
        self.channel = channel
        self.bitrate = bitrate

    def _build_bus(self) -> Any:
        spec = importlib.util.find_spec("can")
        if spec is None:
            raise RuntimeError("python-can is not installed")
        import can

        return can.interface.Bus(channel=self.channel, bustype="usb2can", bitrate=self.bitrate)

    def run(self) -> None:
        try:
            bus = self._build_bus()
        except Exception as exc:  # noqa: BLE001
            # Falls back to simulation if needed
            self.on_update(VehicleUpdate(ambient_assist_message=f"CAN unavailable: {exc}"))
            return

        for msg in bus:
            if self.should_stop():
                break
            update = self._decode_message(msg)
            if update:
                self.on_update(update)
            time.sleep(0.01)

    def _decode_message(self, msg: Any) -> VehicleUpdate | None:
        # Example decoding logic for BCM frames. Adjust IDs for the Vivaro.
        if msg.arbitration_id == 0x180:  # example speed frame
            speed_mph = int.from_bytes(msg.data[0:2], "big") * 0.01
            rpm = int.from_bytes(msg.data[2:4], "big")
            battery = msg.data[4]
            indicator_raw = msg.data[5] & 0x03
            indicator = {
                0: IndicatorState.OFF,
                1: IndicatorState.LEFT,
                2: IndicatorState.RIGHT,
                3: IndicatorState.HAZARD,
            }.get(indicator_raw, IndicatorState.OFF)
            door_open = bool(msg.data[5] & 0x10)
            return VehicleUpdate(
                speed_mph=speed_mph,
                rpm=rpm,
                battery_level=battery,
                indicator=indicator,
                door_open=door_open,
            )
        return None
