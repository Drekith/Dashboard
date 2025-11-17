import importlib.util
import time

from dashboard.providers.base import DataProvider
from dashboard.state import VehicleState


class KLineProvider(DataProvider):
    """Reads ISO9141/K-line frames via an ELM327-compatible USB adapter."""

    def __init__(self, port: str, baudrate: int, on_update):
        super().__init__(on_update)
        self.port = port
        self.baudrate = baudrate

    def _open_serial(self):
        spec = importlib.util.find_spec("serial")
        if spec is None:
            raise RuntimeError("pyserial is not installed")
        import serial

        return serial.Serial(self.port, self.baudrate, timeout=1)

    def run(self) -> None:
        try:
            ser = self._open_serial()
        except Exception as exc:  # noqa: BLE001
            self.on_update(VehicleState(ambient_assist_message=f"K-Line unavailable: {exc}"))
            return

        self._initialize_elm(ser)
        while not self.should_stop():
            ser.write(b"010C\r")  # RPM
            rpm_line = ser.readline().decode(errors="ignore")
            ser.write(b"010D\r")  # Speed
            speed_line = ser.readline().decode(errors="ignore")

            update = VehicleState(
                rpm=self._parse_pid_value(rpm_line, fallback=self.on_update.__self__.state.rpm),
                speed_mph=self._parse_pid_value(speed_line, scale=1.0, fallback=self.on_update.__self__.state.speed_mph),
            )
            self.on_update(update)
            time.sleep(1.0)

    def _initialize_elm(self, ser) -> None:
        commands = [b"ATZ\r", b"ATE0\r", b"ATL0\r", b"ATS0\r", b"ATSP0\r"]
        for cmd in commands:
            ser.write(cmd)
            time.sleep(0.2)
            ser.readline()

    def _parse_pid_value(self, line: str, scale: float = 0.25, fallback: float | int = 0) -> float:
        try:
            parts = [int(p, 16) for p in line.strip().split()[2:4]]
            value = ((parts[0] * 256) + parts[1]) * scale
            return value
        except Exception:  # noqa: BLE001
            return fallback
