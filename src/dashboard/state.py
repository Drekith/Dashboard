from dataclasses import dataclass
from enum import Enum
from typing import Optional


class IndicatorState(str, Enum):
    OFF = "off"
    LEFT = "left"
    RIGHT = "right"
    HAZARD = "hazard"


@dataclass
class VehicleUpdate:
    speed_mph: Optional[float] = None
    rpm: Optional[int] = None
    battery_level: Optional[int] = None
    nav_distance_feet: Optional[int] = None
    nav_heading: Optional[str] = None
    indicator: Optional[IndicatorState] = None
    door_open: Optional[bool] = None
    ambient_temp_f: Optional[float] = None
    drive_mode: Optional[str] = None
    radio_station: Optional[str] = None
    ambient_assist_message: Optional[str] = None


@dataclass
class VehicleState:
    speed_mph: float = 0.0
    rpm: int = 0
    battery_level: int = 0
    nav_distance_feet: Optional[int] = None
    nav_heading: Optional[str] = None
    indicator: IndicatorState = IndicatorState.OFF
    door_open: bool = False
    ambient_temp_f: float = 72.0
    drive_mode: str = "ECO"
    radio_station: str = "Radio"
    ambient_assist_message: str = ""  # short hint text

    def apply_update(self, update: VehicleUpdate) -> None:
        for key, value in update.__dict__.items():
            if value is not None:
                setattr(self, key, value)

    def formatted_heading(self) -> str:
        return self.nav_heading or ""

    def formatted_nav_distance(self) -> str:
        if self.nav_distance_feet is None:
            return ""
        if self.nav_distance_feet >= 5280:
            miles = self.nav_distance_feet / 5280
            return f"{miles:.1f} mi"
        return f"{self.nav_distance_feet} ft"
