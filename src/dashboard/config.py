from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass
from typing import List


def _list_serial_ports():
    spec = importlib.util.find_spec("serial")
    if spec is None:
        return []
    from serial.tools import list_ports

    return list_ports.comports()


def auto_detect_kline_port(env_value: str = "") -> str:
    if env_value:
        return env_value
    for port in _list_serial_ports():
        description = port.description.upper()
        if "ELM" in description or "OBD" in description or "USB" in description:
            return port.device
    return ""


def available_serial_labels() -> List[str]:
    labels: List[str] = []
    for port in _list_serial_ports():
        labels.append(f"{port.device} ({port.description})")
    return labels


def extract_device(label: str) -> str:
    return label.split()[0] if label else ""


@dataclass
class ProviderConfig:
    can_channel: str = ""
    can_bitrate: int = 500000
    bcm_can_channel: str = ""
    bcm_can_bitrate: int = 33333
    kline_port: str = ""
    kline_baud: int = 10400

    @classmethod
    def from_env(cls) -> "ProviderConfig":
        return cls(
            can_channel=os.getenv("CAN_CHANNEL", ""),
            can_bitrate=int(os.getenv("CAN_BITRATE", "500000")),
            bcm_can_channel=os.getenv("BCM_CAN_CHANNEL", os.getenv("CAN_CHANNEL", "")),
            bcm_can_bitrate=int(os.getenv("BCM_CAN_BITRATE", os.getenv("CAN_BITRATE", "33333"))),
            kline_port=auto_detect_kline_port(os.getenv("KLINE_PORT", "")),
            kline_baud=int(os.getenv("KLINE_BAUD", "10400")),
        )
