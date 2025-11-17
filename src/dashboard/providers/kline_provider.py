import importlib.util
import time

from dashboard.providers.base import DataProvider
from dashboard.state import VehicleUpdate


class KLineProvider(DataProvider):
    """Reads ISO9141/K-line frames via an ELM327-compatible USB adapter."""

    def __init__(self, port: str, baudrate: int, on_update):
        super().__init__(on_update)
        self.port = port
        self.baudrate = baudrate
        self.last_rpm: float | None = None
        self.last_speed: float | None = None

    def _open_serial(self):
        spec = importlib.util.find_spec("serial")
        if spec is None:
            raise RuntimeError("pyserial is not installed")
        import serial

        return serial.Serial(self.port, self.baudrate, timeout=1)

    def probe(self) -> bool:
        try:
            ser = self._open_serial()
            ser.close()
            return True
        except Exception:
            return False

    def run(self) -> None:
        try:
            ser = self._open_serial()
        except Exception as exc:  # noqa: BLE001
            self.on_update(VehicleUpdate(ambient_assist_message=f"K-Line unavailable: {exc}"))
            return

        self._initialize_elm(ser)
        while not self.should_stop():
            ser.write(b"010C\r")  # RPM
            rpm_line = ser.readline().decode(errors="ignore")
            ser.write(b"010D\r")  # Speed
            speed_line = ser.readline().decode(errors="ignore")

            rpm_value = self._parse_pid_value(rpm_line, scale=0.25, fallback=self.last_rpm or 0)
            speed_value = self._parse_pid_value(speed_line, scale=1.0, fallback=self.last_speed or 0)
            self.last_rpm, self.last_speed = rpm_value, speed_value

            update = VehicleUpdate(
                rpm=int(rpm_value),
                speed_mph=float(speed_value),
            )
            self.on_update(update)
            time.sleep(1.0)

    def _initialize_elm(self, ser) -> None:
        commands = [b"ATZ\r", b"ATE0\r", b"ATL0\r", b"ATS0\r", b"ATSP0\r"]
        for cmd in commands:
            ser.write(cmd)
            time.sleep(0.2)
            ser.readline()

    def _parse_pid_value(self, line: str, scale: float, fallback: float | int = 0) -> float:
        try:
            parts = [int(p, 16) for p in line.strip().split()[2:4]]
            value = ((parts[0] * 256) + parts[1]) * scale
            return value
        except Exception:  # noqa: BLE001
            return float(fallback)
