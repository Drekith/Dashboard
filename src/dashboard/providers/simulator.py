import math
import random
import time

from dashboard.providers.base import DataProvider
from dashboard.state import IndicatorState, VehicleState


class SimulatorProvider(DataProvider):
    """Generates realistic-looking demo data when hardware is unavailable."""

    def __init__(self, on_update, refresh_rate: float = 0.2):
        super().__init__(on_update)
        self.refresh_rate = refresh_rate
        self._angle = 0.0

    def run(self) -> None:
        while not self.should_stop():
            self._angle += 0.05
            speed = max(0.0, 45 + math.sin(self._angle) * 20)
            rpm = int(2000 + math.sin(self._angle * 1.6) * 800)
            battery = 70 + int(math.sin(self._angle * 0.3) * 5)
            indicator_cycle = [IndicatorState.OFF, IndicatorState.LEFT, IndicatorState.RIGHT]
            indicator = indicator_cycle[int(self._angle) % len(indicator_cycle)]
            door_open = random.random() < 0.05
            nav_distance = max(200, int(1200 - (self._angle * 25) % 1200))
            nav_heading = random.choice(["1", "2", "3"])

            update = VehicleState(
                speed_mph=speed,
                rpm=rpm,
                battery_level=battery,
                indicator=indicator,
                door_open=door_open,
                nav_distance_feet=nav_distance,
                nav_heading=nav_heading,
                ambient_assist_message="Demo mode"
                if indicator is IndicatorState.OFF
                else "Check mirrors",
            )
            self.on_update(update)
            time.sleep(self.refresh_rate)
