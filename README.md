# Vivaro Dashboard

A Windows-focused dashboard that mimics the modern cluster shown in the mock image and can read data from:

- A Waveshare USB-to-CAN-A adapter for BCM / CAN bus data (door status, indicators, speed, battery).
- An ELM327-compatible USB adapter (K-line/ISO9141) for engine PIDs such as speed and RPM.
- A built-in simulator for development without hardware.

## Features

- Real-time UI built with PySide6 that mirrors the layout of the provided cluster mock: driver zone on the left and assist tiles on the right, now with animated gauges and a style switcher.
- Modular data providers for CAN, K-Line, and simulated data. Providers run in background threads and merge into a shared `VehicleState`.
- Graceful degradation: if hardware is missing, a simulator keeps the UI alive while surfacing status messages.
- Auto-calibrated gauges that expand their scale and tick intervals to stay synchronized with live speed/RPM readings.
- OEM-inspired visuals with animated speed/RPM gauges and configurable colorways ("oem", "neo", "contrast", "mono") tuned for the Vivaro cluster mock, paired with new digital hero cards for instant glanceable speed/RPM plus system chips.
- Tabbed navigation with a **Settings** page (hardware status, live COM/baud reconfiguration), an interactive **Layout Editor** with drag-and-drop widget placement, and a **Theme Editor** to craft custom gauge palettes without editing code.
- Touch-friendly controls (large tabs, buttons, combos) plus a quick **Full screen** toggle to maximize usable space on an in-dash display.

## Requirements

- Python 3.11+ on Windows.
- Drivers for your Waveshare USB-to-CAN-A and ELM327 adapters.
- Dependencies listed in `requirements.txt`:
  - `PySide6` for the UI.
  - `python-can` for the Waveshare adapter (`bustype=usb2can`).
  - `pyserial` for the ELM327 USB adapter.

Install them with:

```bash
pip install -r requirements.txt
```

## Running

1. Plug in the adapters and note their Windows COM names (e.g., `COM3` for CAN, `COM4` for ELM327). Export them as environment variables before launching. If `KLINE_PORT` is not set, the app will try to auto-detect the first ELM/OBD USB serial device:

```bash
set CAN_CHANNEL=COM3
set KLINE_PORT=COM4
```

2. From the repo root, launch the dashboard:

```bash
python -m dashboard.main
```

Startup will probe for the configured devices. If initialization fails or no hardware is detected, the simulator will activate automatically and display a brief status message in the cluster.

### In-app port configuration

- Open the **Settings** tab to edit CAN channel/bitrate and K-Line port/baud while the app is running. Click **Apply port settings** to rebuild the providers with the new COM assignments without restarting.
- Use **Auto-detect K-Line** to prefill the first detected ELM/OBD serial device; detected ports are also listed in the dropdown for quick selection.

## Customizing decoding

- **CAN (BCM):** Update `_decode_message` in `src/dashboard/providers/can_provider.py` with the Vivaro-specific arbitration IDs and byte layouts for speed, battery, indicators, and doors.
- **K-line (ELM327):** Adjust the PID queries in `src/dashboard/providers/kline_provider.py` if your adapter uses different commands. The defaults query RPM (`010C`) and speed (`010D`).

## Project layout

- `src/dashboard/state.py` – `VehicleState` dataclass and indicator enums.
- `src/dashboard/providers/` – Hardware and simulator data providers.
- `src/dashboard/services/data_pipeline.py` – Thread-safe state aggregation.
- `src/dashboard/ui/main_window.py` – PySide6 UI with animated gauges, assist/status tiles, and settings/theme tabs.
- `src/dashboard/ui/gauge.py` – Reusable animated gauge widget with selectable styles.
- `src/dashboard/main.py` – Entry point that wires providers and starts the app.

## Notes for the 2003 Vauxhall Vivaro

- Typical CAN bitrate is 500 kbps; adjust `bitrate` in `CanProvider` if your van differs.
- The placeholder arbitration ID `0x180` should be replaced with the actual BCM frame IDs from your vehicle.
- K-line on the Vivaro often runs at 10400 baud. Ensure the ELM327 adapter is configured accordingly.

## Styling and UI customization

- Use the **Gauge style** dropdown in the header to swap between the built-in palettes (oem, neo, contrast, mono) without restarting the app.
- The assist sidebar now focuses on navigation, ambient temperature, battery, and indicator/door status chips, removing unused mock items like radio, drive mode, and altitude displays.
- Open the **Settings** tab to confirm which data providers are active and flip the layout to swap gauge order.
- The **Layout Editor** tab offers presets (standard, swapped, vertical stack), drag-and-drop placement of the hero/gauge/assist/status widgets onto a live grid, and visibility toggles so you can tailor the dashboard footprint.
- Use the **Theme Editor** tab to pick custom colors (track, glow, accent, accent alt, text), name the palette, and apply it live to both gauges. Custom palettes are added to the style dropdown for reuse.
- Tap **Full screen** on the Dashboard tab to hide chrome for a cleaner, OEM-like touchscreen experience; tap again to return.
- The new hero row shows large digital speed/RPM readouts and battery/ambient/route chips sized for finger taps.
