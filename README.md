# Vivaro Dashboard

A Windows-focused dashboard that mimics the modern cluster shown in the mock image and can read data from:

- A Waveshare USB-to-CAN-A adapter for BCM data (door status, indicators, speed, battery) when wired behind the dash.
- A dedicated BCM provider tuned for the low-speed body network when you tap the BCM lines behind the dash on a 2003 Vivaro 1.9DTi.
- An ELM327-compatible USB adapter (K-line/ISO9141) for engine PIDs such as speed and RPM.
- A built-in simulator for development without hardware.

## Features

- Real-time UI built with PySide6 that mirrors the layout of the provided cluster mock: driver zone on the left and assist tiles on the right, now with animated gauges and a style switcher.
- Modular data providers for BCM CAN (Waveshare only), K-Line (ELM only), and simulated data. Providers run in background threads and merge into a shared `VehicleState`.
- Graceful degradation: if hardware is missing, a simulator keeps the UI alive while surfacing status messages.
- Auto-calibrated gauges that expand their scale and tick intervals to stay synchronized with live speed/RPM readings.
- OEM-inspired visuals with animated speed/RPM gauges and configurable colorways ("oem", "neo", "contrast", "mono") tuned for the Vivaro cluster mock, paired with new digital hero cards for instant glanceable speed/RPM plus system chips.
- Tabbed navigation with a **Settings** page (hardware status, per-provider pop-up config dialogs, simulator toggle), an interactive **Layout Editor** with drag-and-drop widget placement, and a **Theme Editor** to craft custom gauge palettes without editing code.
- Touch-friendly controls (large tabs, buttons, combos) plus a quick **Full screen** toggle to maximize usable space on an in-dash display.

## Requirements

- Python 3.11+ on Windows.
- Drivers for your Waveshare USB-to-CAN-A and ELM327 adapters.
- Dependencies listed in `requirements.txt`:
  - `PySide6` for the UI.
  - `python-can` for the Waveshare adapter (`bustype=usb2can`).
  - `pyserial` for the ELM327 USB adapter.
  - `pywin32` (Windows only) to provide `win32com.client`, which `python-can` uses for USB-to-CAN on Waveshare adapters.

Install them with:

```bash
pip install -r requirements.txt
```

## Running

1. Plug in the adapters and note their Windows COM names (e.g., `COM5` for the Waveshare BCM link, `COM4` for the ELM327). Export them as environment variables before launching. If `KLINE_PORT` is not set, the app will try to auto-detect the first ELM/OBD USB serial device and BCM will fall back to COM5 or any detected Waveshare:

```bash
set BCM_CAN_CHANNEL=COM5
set BCM_CAN_BITRATE=33333
set KLINE_PORT=COM4
```

2. From the repo root, launch the dashboard:

```bash
python -m dashboard.main
```

Startup will probe for the configured devices. If initialization fails or no hardware is detected, the simulator will activate automatically (unless you disable it in Settings) and display a brief status message in the cluster.

> Windows note: if you see an error about `win32com.client` when starting a Waveshare USB-to-CAN adapter, reinstall dependencies so `pywin32` is present: `pip install -r requirements.txt`.

### In-app provider configuration

- Tap **Ports** (header quick action) or open the **Settings** tab, then click **Open provider menu…** to launch the consolidated pop-out dialog for hardware. BCM and K-Line live in one place so you can update COM ports/bitrates together.
- Use **Detect Waveshare** (BCM) or **Detect ELM** (K-Line) to auto-fill the first matching adapter. Detected serial ports also appear in the dropdowns for quick selection.
- A **Simulator fallback/preview** checkbox in the dialog lets you toggle the built-in simulator; when disabled and no hardware is active, the UI will surface a warning instead of injecting simulated frames.

## Customizing decoding

- **BCM CAN:** Update `_decode_message` in `src/dashboard/providers/bcm_can_provider.py` with the Vivaro-specific arbitration IDs and byte layouts for door, indicator, ambient, and BCM speed frames when wired to the BCM behind the dash.
- **K-line (ELM327):** Adjust the PID queries in `src/dashboard/providers/kline_provider.py` if your adapter uses different commands. The defaults query RPM (`010C`) and speed (`010D`).

## Project layout

- `src/dashboard/state.py` – `VehicleState` dataclass and indicator enums.
- `src/dashboard/providers/` – Hardware and simulator data providers.
- `src/dashboard/services/data_pipeline.py` – Thread-safe state aggregation.
- `src/dashboard/ui/main_window.py` – PySide6 UI with animated gauges, assist/status tiles, and settings/theme tabs.
- `src/dashboard/ui/gauge.py` – Reusable animated gauge widget with selectable styles.
- `src/dashboard/main.py` – Entry point that wires providers and starts the app.

## Notes for the 2003 Vauxhall Vivaro

- The BCM behind the dash commonly runs at ~33.3 kbps on the low-speed body network; set `BCM_CAN_BITRATE` to match your measurement (defaults to 33333).
- The placeholder arbitration IDs (e.g., `0x180`, `0x1A0`) in the BCM provider should be replaced with the actual BCM frame IDs from your vehicle.
- K-line on the Vivaro often runs at 10400 baud. Ensure the ELM327 adapter is configured accordingly.

## Styling and UI customization

- Use the **Gauge style** dropdown in the header to swap between the built-in palettes (oem, neo, contrast, mono) without restarting the app.
- The assist sidebar now focuses on navigation, ambient temperature, battery, and indicator/door status chips, removing unused mock items like radio, drive mode, and altitude displays.
- Open the **Settings** tab to confirm which data providers are active and flip the layout to swap gauge order.
- The **Layout Editor** tab offers presets (standard, swapped, vertical stack), drag-and-drop placement of the hero/gauge/assist/status widgets onto a live grid, and visibility toggles so you can tailor the dashboard footprint. Press and hold a tile to start dragging on touchscreens, then drop it into a slot.
- Use the **Theme Editor** tab to pick custom colors (track, glow, accent, accent alt, text), name the palette, and apply it live to both gauges. Custom palettes are added to the style dropdown for reuse.
- Tap **Full screen** on the Dashboard tab to hide chrome for a cleaner, OEM-like touchscreen experience; tap again to return.
- The new hero row shows large digital speed/RPM readouts and battery/ambient/route chips sized for finger taps.
