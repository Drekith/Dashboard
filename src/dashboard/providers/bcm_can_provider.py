import importlib.util
import time
from typing import Any

from dashboard.providers.base import DataProvider
from dashboard.state import IndicatorState, VehicleUpdate


class BcmCanProvider(DataProvider):
    """Dedicated BCM reader for Vivaro low-speed CAN via Waveshare USB-to-CAN-A."""

    def __init__(self, channel: str, bitrate: int, on_update):
        super().__init__(on_update)
        self.channel = channel
        self.bitrate = bitrate

    def _build_bus(self) -> Any:
        self._require_win32com()
        spec = importlib.util.find_spec("can")
        if spec is None:
            raise RuntimeError("python-can is not installed")
        import can

        return can.interface.Bus(
            channel=self.channel,
            bustype="usb2can",
            bitrate=self.bitrate,
        )

    def probe(self) -> bool:
        try:
            bus = self._build_bus()
            bus.shutdown()
            return True
        except Exception:
            return False

    def run(self) -> None:
        try:
            bus = self._build_bus()
        except Exception as exc:  # noqa: BLE001
            self.on_update(
                VehicleUpdate(
                    ambient_assist_message=f"BCM CAN unavailable: {exc}"
                )
            )
            return

        for msg in bus:
            if self.should_stop():
                break
            update = self._decode_message(msg)
            if update:
                self.on_update(update)
            time.sleep(0.01)

    def _decode_message(self, msg: Any) -> VehicleUpdate | None:
        """Parse a handful of BCM-focused frames.

        These defaults are intentionally conservative and should be tweaked for the
        Vivaro's exact BCM mapping. They cover the common speed / RPM cluster frame
        plus a body status frame that carries doors, indicators, and ambient temp
        found on many Renault/Nissan-era vans of this generation.
        """

        # Cluster-like payload: speed / RPM / battery / indicator / doors
        if msg.arbitration_id == 0x180 and msg.dlc >= 6:
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

        # Body status payload: door ajar + ambient temperature + hazard/indicator
        if msg.arbitration_id == 0x1A0 and msg.dlc >= 3:
            door_mask = msg.data[0] & 0x0F
            door_open = bool(door_mask)
            ambient_c = msg.data[1] - 40  # simple signed byte offset
            ambient_f = ambient_c * 9 / 5 + 32
            indicator_raw = msg.data[2] & 0x03
            indicator = {
                0: IndicatorState.OFF,
                1: IndicatorState.LEFT,
                2: IndicatorState.RIGHT,
                3: IndicatorState.HAZARD,
            }.get(indicator_raw, IndicatorState.OFF)
            return VehicleUpdate(
                door_open=door_open,
                ambient_temp_f=ambient_f,
                indicator=indicator,
            )

        return None
