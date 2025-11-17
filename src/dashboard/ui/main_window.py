from __future__ import annotations

import textwrap

from PySide6 import QtCore, QtGui, QtWidgets

from dashboard.config import (
    ProviderConfig,
    available_serial_labels,
    extract_device,
)
from dashboard.services.data_pipeline import DataPipeline
from dashboard.state import IndicatorState
from dashboard.ui.gauge import GaugeWidget


GLOBAL_STYLES = textwrap.dedent(
    """
    QWidget { background-color: #03050c; color: #e5e7eb; font-family: 'Segoe UI', sans-serif; }
    QMainWindow {
        background: radial-gradient(circle at 30% 20%, #0d172d, #04060d 55%, #02030b 70%);
    }
    QLabel[role="title"] { font-size: 34px; font-weight: 800; letter-spacing: 0.6px; }
    QLabel[role="subtitle"] { font-size: 20px; color: #cbd5e1; }
    QLabel[role="value"] { font-size: 26px; font-weight: 700; }
    QLabel[role="label"] { font-size: 14px; color: #9ba9bd; text-transform: uppercase; letter-spacing: 1.4px; }
    .panel { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0a0e16, stop:1 #0f172a); border: 1px solid #1f2937; border-radius: 18px; padding: 18px; }
    .glass { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 20px; padding: 16px; }
    .hero { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0f1828, stop:1 #0a1021); border: 1px solid rgba(255,255,255,0.06); border-radius: 18px; padding: 18px 20px; }
    .chip { background: rgba(148, 163, 184, 0.18); border-radius: 14px; padding: 10px 14px; }
    QComboBox, QPushButton, QLineEdit { background: #0f172a; padding: 12px 16px; border: 1px solid #1f2937; border-radius: 14px; color: #e2e8f0; font-size: 16px; }
    QComboBox QAbstractItemView { background: #0f172a; selection-background-color: #1f2937; }
    QPushButton { background: #162032; font-weight: 600; }
    QPushButton:hover { background: #1e2c45; }
    QTabWidget::pane { border: none; }
    QTabBar::tab { background: transparent; color: #cbd5e1; padding: 14px 22px; margin: 0 4px; border-radius: 14px 14px 0 0; font-size: 16px; }
    QTabBar::tab:selected { background: #111827; color: #f8fafc; border: 1px solid #1f2937; border-bottom: none; }
    QListWidget[class="panel"] { border: 1px solid #1f2937; border-radius: 12px; background: #0b1220; }
    QListWidget[class="panel"]::item { padding: 12px; font-size: 15px; }
    .muted { color: #94a3b8; font-size: 14px; letter-spacing: 0.8px; }
    .hero-value { font-size: 58px; font-weight: 800; }
    .hero-unit { color: #9ca3af; font-weight: 600; margin-left: 4px; }
    """
)


MIME_TYPE = "application/x-dashboard-section"


class DraggableTile(QtWidgets.QFrame):
    def __init__(self, key: str, title: str, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.key = key
        self.setProperty("class", "panel")
        self.setCursor(QtCore.Qt.OpenHandCursor)
        self._press_pos: QtCore.QPoint | None = None
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        label = QtWidgets.QLabel(title)
        label.setProperty("role", "subtitle")
        layout.addWidget(label)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:  # noqa: N802
        if event.button() == QtCore.Qt.LeftButton:
            self._press_pos = event.pos()
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:  # noqa: N802
        if not (event.buttons() & QtCore.Qt.LeftButton):
            return super().mouseMoveEvent(event)
        if self._press_pos is None:
            return super().mouseMoveEvent(event)
        if (event.pos() - self._press_pos).manhattanLength() < QtWidgets.QApplication.startDragDistance():
            return super().mouseMoveEvent(event)

        drag = QtGui.QDrag(self)
        mime = QtCore.QMimeData()
        mime.setData(MIME_TYPE, self.key.encode())
        drag.setMimeData(mime)
        drag.setPixmap(self.grab())
        drag.exec(QtCore.Qt.MoveAction)
        super().mouseMoveEvent(event)


class DropZone(QtWidgets.QFrame):
    dropped = QtCore.Signal(str, str)

    def __init__(self, slot: str, title: str, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.slot = slot
        self.setAcceptDrops(True)
        self.setProperty("class", "glass")
        self.setMinimumHeight(120)
        self._default_style = self.styleSheet()
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setProperty("role", "label")
        layout.addWidget(self.title_label)
        self.content_label = QtWidgets.QLabel("Drop widget here")
        self.content_label.setProperty("role", "subtitle")
        layout.addWidget(self.content_label)
        layout.addStretch()

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasFormat(MIME_TYPE):
            event.acceptProposedAction()
            self.setStyleSheet("border: 2px dashed #4ade80;")

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:  # noqa: N802
        if event.mimeData().hasFormat(MIME_TYPE):
            event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:  # noqa: N802
        if event.mimeData().hasFormat(MIME_TYPE):
            key = bytes(event.mimeData().data(MIME_TYPE)).decode()
            self.dropped.emit(self.slot, key)
            event.acceptProposedAction()
        self.setStyleSheet(self._default_style)

    def dragLeaveEvent(self, event: QtGui.QDragLeaveEvent) -> None:  # noqa: N802
        self.setStyleSheet(self._default_style)
        super().dragLeaveEvent(event)

    def set_assigned(self, text: str) -> None:
        self.content_label.setText(text)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(
        self,
        pipeline: DataPipeline,
        config: ProviderConfig,
        reconfigure_callback,
        auto_detect_kline,
    ):
        super().__init__()
        self.pipeline = pipeline
        self.current_config = config
        self.reconfigure_callback = reconfigure_callback
        self.auto_detect_kline = auto_detect_kline
        self.setWindowTitle("Vivaro Cluster")
        self.setMinimumSize(1280, 720)
        self.setStyleSheet(GLOBAL_STYLES)
        self.setAttribute(QtCore.Qt.WA_AcceptTouchEvents, True)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setTabPosition(QtWidgets.QTabWidget.North)
        self.tabs.setDocumentMode(True)
        self.tabs.setIconSize(QtCore.QSize(28, 28))
        self.tabs.tabBar().setExpanding(True)

        self.dashboard_tab = self._build_dashboard_tab()
        self.settings_tab = self._build_settings_tab()
        self.theme_tab = self._build_theme_editor_tab()
        self.layout_tab = self._build_layout_editor_tab()

        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.settings_tab, "Settings")
        self.tabs.addTab(self.theme_tab, "Theme Editor")
        self.tabs.addTab(self.layout_tab, "Layout Editor")

        self.setCentralWidget(self.tabs)

        self._apply_touch_targets()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.refresh_ui)
        self.timer.start(150)

    def _build_dashboard_tab(self) -> QtWidgets.QWidget:
        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)
        layout.setSpacing(18)
        layout.setContentsMargins(20, 20, 20, 20)

        header_row = QtWidgets.QHBoxLayout()
        header_row.setSpacing(12)

        brand = QtWidgets.QLabel("Vivaro OEM")
        brand.setProperty("role", "title")
        brand.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        header_row.addWidget(brand)

        self.heading_label = QtWidgets.QLabel("⬆")
        self.heading_label.setProperty("role", "title")
        self.heading_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        header_row.addWidget(self.heading_label)

        self.nav_distance_label = QtWidgets.QLabel("")
        self.nav_distance_label.setProperty("role", "subtitle")
        header_row.addWidget(self.nav_distance_label)
        header_row.addStretch()

        style_label = QtWidgets.QLabel("Gauge style")
        style_label.setProperty("role", "label")
        header_row.addWidget(style_label)

        self.style_selector = QtWidgets.QComboBox()
        self.style_selector.addItems(["oem", "neo", "contrast", "mono"])
        self.style_selector.setCurrentText("oem")
        self.style_selector.currentTextChanged.connect(self._on_style_changed)
        header_row.addWidget(self.style_selector)

        self.fullscreen_btn = QtWidgets.QPushButton("Full screen")
        self.fullscreen_btn.clicked.connect(self._toggle_fullscreen)
        header_row.addWidget(self.fullscreen_btn)

        self.quick_ports_btn = QtWidgets.QPushButton("Ports")
        self.quick_ports_btn.clicked.connect(lambda: self._jump_to_tab(self.settings_tab))
        header_row.addWidget(self.quick_ports_btn)

        self.quick_layout_btn = QtWidgets.QPushButton("Layout")
        self.quick_layout_btn.clicked.connect(lambda: self._jump_to_tab(self.layout_tab))
        header_row.addWidget(self.quick_layout_btn)

        layout.addLayout(header_row)

        self.dashboard_grid = QtWidgets.QGridLayout()
        self.dashboard_grid.setSpacing(18)
        self.dashboard_grid.setColumnStretch(0, 1)
        self.dashboard_grid.setColumnStretch(1, 1)
        layout.addLayout(self.dashboard_grid)

        self.hero_widget = self._build_hero_row()

        self.gauges_row = QtWidgets.QHBoxLayout()
        self.gauges_row.setSpacing(18)
        self.gauges_row.setDirection(QtWidgets.QBoxLayout.LeftToRight)

        self.speed_gauge = GaugeWidget("Speed", "mph", 120, style="oem")
        self.rpm_gauge = GaugeWidget("RPM", "rpm", 7000, style="oem")
        gauge_frame = QtWidgets.QFrame()
        gauge_frame.setProperty("class", "glass")
        gauge_frame_layout = QtWidgets.QHBoxLayout(gauge_frame)
        gauge_frame_layout.setSpacing(18)
        gauge_frame_layout.addLayout(self.gauges_row)

        self.gauges_row.addWidget(self.speed_gauge, 1)
        self.gauges_row.addWidget(self.rpm_gauge, 1)

        self.gauge_widget = gauge_frame

        self.assist_panel = self._build_assist_panel()
        self.status_panel = self._build_status_panel()

        self.section_widgets = {
            "hero": self.hero_widget,
            "gauges": self.gauge_widget,
            "assist": self.assist_panel,
            "status": self.status_panel,
        }
        self.slot_positions: dict[str, tuple[int, int, int, int]] = {
            "slot1": (0, 0, 1, 2),
            "slot2": (1, 0, 1, 2),
            "slot3": (2, 0, 1, 1),
            "slot4": (2, 1, 1, 1),
        }
        self.slot_assignments: dict[str, str] = {
            "slot1": "hero",
            "slot2": "gauges",
            "slot3": "assist",
            "slot4": "status",
        }
        self.drop_zones: dict[str, DropZone] = {}
        self._apply_slot_assignments()
        return central

    def _build_hero_row(self) -> QtWidgets.QWidget:
        frame = QtWidgets.QFrame()
        frame.setProperty("class", "glass")
        row = QtWidgets.QHBoxLayout(frame)
        row.setSpacing(14)

        self.speed_hero = self._make_hero_card("Speed", "mph", "0")
        row.addWidget(self.speed_hero)

        self.rpm_hero = self._make_hero_card("Engine", "rpm", "0")
        row.addWidget(self.rpm_hero)

        side = QtWidgets.QVBoxLayout()
        side.setSpacing(10)
        side.setContentsMargins(0, 0, 0, 0)

        self.battery_hero = self._make_small_chip("Battery", "0%", "🔋")
        self.temp_hero = self._make_small_chip("Ambient", "--°F", "🌡")
        self.route_hero = self._make_small_chip("Route", "Waiting", "🧭")

        for chip in [self.battery_hero, self.temp_hero, self.route_hero]:
            side.addWidget(chip)

        row.addLayout(side, 1)

        return frame

    def _build_settings_tab(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QtWidgets.QLabel("System settings")
        title.setProperty("role", "title")
        layout.addWidget(title)

        subtitle = QtWidgets.QLabel(
            "Review detected hardware and switch dashboard layout preferences."
        )
        subtitle.setProperty("role", "subtitle")
        layout.addWidget(subtitle)

        provider_label = QtWidgets.QLabel("Data providers")
        provider_label.setProperty("role", "label")
        layout.addWidget(provider_label)

        self.provider_list = QtWidgets.QListWidget()
        self.provider_list.setProperty("class", "panel")
        self.provider_list.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        layout.addWidget(self.provider_list)
        self._populate_provider_list()

        self.hardware_status_label = QtWidgets.QLabel("Status: Monitoring")
        self.hardware_status_label.setProperty("role", "subtitle")
        layout.addWidget(self.hardware_status_label)

        port_label = QtWidgets.QLabel("Provider configuration")
        port_label.setProperty("role", "label")
        layout.addWidget(port_label)

        self.port_summary = QtWidgets.QLabel(self._port_summary_text())
        self.port_summary.setProperty("class", "muted")
        layout.addWidget(self.port_summary)

        button_grid = QtWidgets.QGridLayout()
        button_grid.setHorizontalSpacing(12)
        button_grid.setVerticalSpacing(8)

        self.can_config_btn = QtWidgets.QPushButton("Configure CAN…")
        self.can_config_btn.clicked.connect(self._open_can_dialog)
        button_grid.addWidget(self.can_config_btn, 0, 0)

        self.bcm_config_btn = QtWidgets.QPushButton("Configure BCM CAN…")
        self.bcm_config_btn.clicked.connect(self._open_bcm_dialog)
        button_grid.addWidget(self.bcm_config_btn, 0, 1)

        self.kline_config_btn = QtWidgets.QPushButton("Configure K-Line…")
        self.kline_config_btn.clicked.connect(self._open_kline_dialog)
        button_grid.addWidget(self.kline_config_btn, 1, 0)

        self.sim_toggle = QtWidgets.QCheckBox("Enable simulator fallback and preview")
        self.sim_toggle.setChecked(self.current_config.enable_simulator)
        self.sim_toggle.stateChanged.connect(self._toggle_simulation_mode)
        button_grid.addWidget(self.sim_toggle, 1, 1)

        layout.addLayout(button_grid)

        layout_mode_label = QtWidgets.QLabel("Layout mode")
        layout_mode_label.setProperty("role", "label")
        layout.addWidget(layout_mode_label)

        self.layout_mode_combo = QtWidgets.QComboBox()
        self.layout_mode_combo.addItems(
            ["Standard", "Swap speed / RPM", "Vertical stack"]
        )
        self.layout_mode_combo.currentTextChanged.connect(self._apply_layout_choice)
        layout.addWidget(self.layout_mode_combo)

        layout.addStretch()
        return panel

    def _build_theme_editor_tab(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QtWidgets.QLabel("Layout & theme editor")
        title.setProperty("role", "title")
        layout.addWidget(title)

        subtitle = QtWidgets.QLabel(
            "Craft a custom palette for the animated gauges and preview instantly."
        )
        subtitle.setProperty("role", "subtitle")
        layout.addWidget(subtitle)

        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignRight)

        self.theme_name_input = QtWidgets.QLineEdit("custom")
        form.addRow("Theme name", self.theme_name_input)

        self.theme_inputs: dict[str, QtWidgets.QLineEdit] = {}
        for key in ["track", "glow", "accent", "accent_alt", "text"]:
            color_row = QtWidgets.QHBoxLayout()
            line_edit = QtWidgets.QLineEdit(GaugeWidget.STYLES["oem"][key])
            line_edit.setPlaceholderText("#rrggbb")
            self.theme_inputs[key] = line_edit

            choose_btn = QtWidgets.QPushButton("Pick")
            choose_btn.clicked.connect(lambda _, field=key: self._pick_color(field))

            color_row.addWidget(line_edit)
            color_row.addWidget(choose_btn)
            form.addRow(key.replace("_", " ").title(), color_row)

        layout.addLayout(form)

        self.apply_theme_btn = QtWidgets.QPushButton("Apply to gauges")
        self.apply_theme_btn.clicked.connect(self._apply_custom_theme)
        layout.addWidget(self.apply_theme_btn)

        layout.addStretch()
        return panel

    def _build_layout_editor_tab(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QtWidgets.QLabel("Layout editor")
        title.setProperty("role", "title")
        layout.addWidget(title)

        subtitle = QtWidgets.QLabel(
            "Arrange gauges and panels visually. Use presets or fine-tune visibility."
        )
        subtitle.setProperty("role", "subtitle")
        layout.addWidget(subtitle)

        drag_hint = QtWidgets.QLabel(
            "Drag any widget into a slot below to reposition it on the dashboard."
        )
        drag_hint.setProperty("role", "subtitle")
        layout.addWidget(drag_hint)

        mini_hint = QtWidgets.QLabel(
            "Press and hold a tile, then move it into a slot. Use the presets to reset."
        )
        mini_hint.setProperty("class", "muted")
        layout.addWidget(mini_hint)

        preset_label = QtWidgets.QLabel("Gauge arrangement")
        preset_label.setProperty("role", "label")
        layout.addWidget(preset_label)

        self.layout_preset_combo = QtWidgets.QComboBox()
        self.layout_preset_combo.addItems(
            ["Standard", "Swap speed / RPM", "Vertical stack"]
        )
        self.layout_preset_combo.currentTextChanged.connect(self._apply_layout_choice)
        layout.addWidget(self.layout_preset_combo)

        self.assist_toggle = QtWidgets.QCheckBox("Show navigation & battery cards")
        self.assist_toggle.setChecked(True)
        self.assist_toggle.stateChanged.connect(self._apply_layout_visibility)
        layout.addWidget(self.assist_toggle)

        self.status_toggle = QtWidgets.QCheckBox("Show indicator / door chips")
        self.status_toggle.setChecked(True)
        self.status_toggle.stateChanged.connect(self._apply_layout_visibility)
        layout.addWidget(self.status_toggle)

        tile_row = QtWidgets.QHBoxLayout()
        tile_row.setSpacing(10)
        for key, title in [
            ("hero", "Hero row"),
            ("gauges", "Gauges"),
            ("assist", "Assist cards"),
            ("status", "Status chips"),
        ]:
            tile_row.addWidget(DraggableTile(key, title))
        layout.addLayout(tile_row)

        grid_label = QtWidgets.QLabel("Layout canvas")
        grid_label.setProperty("role", "label")
        layout.addWidget(grid_label)

        canvas = QtWidgets.QGridLayout()
        canvas.setSpacing(12)
        zone_titles = {
            "slot1": "Top wide",
            "slot2": "Mid wide",
            "slot3": "Bottom left",
            "slot4": "Bottom right",
        }
        for slot, (row, col, _, colspan) in self.slot_positions.items():
            zone = DropZone(slot, zone_titles.get(slot, slot.title()))
            zone.dropped.connect(self._on_tile_dropped)
            self.drop_zones[slot] = zone
            canvas.addWidget(zone, row, col, 1, colspan)
        layout.addLayout(canvas)
        self._refresh_dropzones()

        hint = QtWidgets.QLabel(
            "Changes are applied instantly. Use Settings to confirm hardware status."
        )
        hint.setProperty("role", "subtitle")
        layout.addWidget(hint)

        layout.addStretch()
        return panel

    def _build_cluster_panel(self) -> QtWidgets.QWidget:
        # legacy cluster panel removed in favor of animated gauges
        return QtWidgets.QWidget()

    def _build_assist_panel(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QWidget()
        panel.setProperty("class", "panel")
        layout = QtWidgets.QGridLayout(panel)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(14)

        self.nav_panel, self.nav_body = self._make_card("Navigation", "Waiting for route")
        layout.addWidget(self.nav_panel, 0, 0, 1, 2)

        self.temp_panel, self.temp_body = self._make_card("Ambient", "72°F")
        layout.addWidget(self.temp_panel, 1, 0, 1, 1)

        self.battery_panel, self.battery_body = self._make_card("Battery", "0%")
        layout.addWidget(self.battery_panel, 1, 1, 1, 1)

        return panel

    def _build_status_panel(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QWidget()
        panel.setProperty("class", "panel")
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setSpacing(12)

        self.indicator_chip = self._make_chip("Indicators", "Idle")
        layout.addWidget(self.indicator_chip)

        self.door_chip = self._make_chip("Doors", "Closed")
        layout.addWidget(self.door_chip)

        self.assist_chip = self._make_chip("Assist", "")
        layout.addWidget(self.assist_chip)

        layout.addStretch()
        return panel

    def _make_card(self, title: str, value: str) -> tuple[QtWidgets.QFrame, QtWidgets.QLabel]:
        card = QtWidgets.QFrame()
        card.setProperty("class", "panel")
        layout = QtWidgets.QVBoxLayout(card)
        layout.setSpacing(6)

        header = QtWidgets.QLabel(title)
        header.setProperty("role", "label")
        layout.addWidget(header)

        body = QtWidgets.QLabel(value)
        body.setProperty("role", "value")
        layout.addWidget(body)

        return card, body

    def _make_hero_card(self, title: str, unit: str, value: str) -> QtWidgets.QFrame:
        card = QtWidgets.QFrame()
        card.setProperty("class", "hero")
        layout = QtWidgets.QVBoxLayout(card)
        layout.setSpacing(4)
        layout.setContentsMargins(16, 14, 16, 14)

        label = QtWidgets.QLabel(title.upper())
        label.setProperty("class", "muted")
        layout.addWidget(label)

        value_row = QtWidgets.QHBoxLayout()
        value_row.setSpacing(6)

        value_label = QtWidgets.QLabel(value)
        value_label.setProperty("class", "hero-value")
        value_row.addWidget(value_label)

        unit_label = QtWidgets.QLabel(unit.upper())
        unit_label.setProperty("class", "hero-unit")
        value_row.addWidget(unit_label)
        value_row.addStretch()

        layout.addLayout(value_row)

        card.value_label = value_label  # type: ignore[attr-defined]
        card.unit_label = unit_label  # type: ignore[attr-defined]
        return card

    def _make_small_chip(
        self, title: str, value: str, icon: str = ""
    ) -> QtWidgets.QFrame:
        chip = QtWidgets.QFrame()
        chip.setProperty("class", "panel")
        layout = QtWidgets.QHBoxLayout(chip)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        if icon:
            icon_label = QtWidgets.QLabel(icon)
            icon_label.setProperty("role", "subtitle")
            layout.addWidget(icon_label)

        label = QtWidgets.QLabel(title)
        label.setProperty("role", "label")
        layout.addWidget(label)

        value_label = QtWidgets.QLabel(value)
        value_label.setProperty("role", "value")
        layout.addWidget(value_label)
        layout.addStretch()

        chip.value_label = value_label  # type: ignore[attr-defined]
        return chip

    def _make_chip(self, title: str, value: str) -> QtWidgets.QWidget:
        wrapper = QtWidgets.QWidget()
        wrapper.setProperty("class", "chip")
        layout = QtWidgets.QHBoxLayout(wrapper)
        layout.setContentsMargins(10, 6, 10, 6)
        label = QtWidgets.QLabel(title)
        label.setProperty("role", "label")
        layout.addWidget(label)
        value_label = QtWidgets.QLabel(value)
        value_label.setProperty("role", "subtitle")
        layout.addWidget(value_label)
        layout.addStretch()
        wrapper.value_label = value_label  # type: ignore[attr-defined]
        return wrapper

    def refresh_ui(self) -> None:
        state = self.pipeline.snapshot()
        self.speed_gauge.setValue(state.speed_mph)
        self.rpm_gauge.setValue(state.rpm)
        heading_symbol = {"L": "⬅", "R": "➡"}.get(state.formatted_heading(), "⬆")
        self.heading_label.setText(heading_symbol)
        distance = state.formatted_nav_distance()
        self.nav_distance_label.setText(distance)

        indicator_text = {
            IndicatorState.OFF: "Idle",
            IndicatorState.LEFT: "Left",
            IndicatorState.RIGHT: "Right",
            IndicatorState.HAZARD: "Hazard",
        }[state.indicator]
        if state.door_open:
            indicator_text = "Door open" if indicator_text == "Idle" else f"{indicator_text} / Door"
        self.nav_body.setText(f"{heading_symbol} {distance}" if distance else "No route")
        self.temp_body.setText(f"{state.ambient_temp_f:.0f}°F")
        self.battery_body.setText(f"{state.battery_level}%")
        self._update_chip(self.indicator_chip, indicator_text)
        self._update_chip(self.door_chip, "Open" if state.door_open else "Closed")
        assist_text = state.ambient_assist_message or "Monitoring"
        self._update_chip(self.assist_chip, assist_text)
        self.hardware_status_label.setText(f"Status: {assist_text}")

        # hero row mirrors the gauges with a clean digital readout
        self.speed_hero.value_label.setText(f"{state.speed_mph:,.0f}")  # type: ignore[attr-defined]
        self.rpm_hero.value_label.setText(f"{state.rpm:,}")  # type: ignore[attr-defined]
        self.battery_hero.value_label.setText(f"{state.battery_level}%")  # type: ignore[attr-defined]
        self.temp_hero.value_label.setText(f"{state.ambient_temp_f:.0f}°F")  # type: ignore[attr-defined]
        route_text = f"{heading_symbol} {distance}" if distance else "No route"
        self.route_hero.value_label.setText(route_text)  # type: ignore[attr-defined]

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # noqa: N802
        self.pipeline.stop()
        super().closeEvent(event)

    def _update_chip(self, chip: QtWidgets.QWidget, text: str) -> None:
        chip.value_label.setText(text)  # type: ignore[attr-defined]

    def _on_style_changed(self, style_name: str) -> None:
        self.speed_gauge.setStyle(style_name)
        self.rpm_gauge.setStyle(style_name)

    def _populate_provider_list(self) -> None:
        self.provider_list.clear()
        if not self.pipeline.providers:
            self.provider_list.addItem(
                "No active providers. Enable simulator or configure ports."
            )
            return
        for provider in self.pipeline.providers:
            name = provider.__class__.__name__
            details: list[str] = []
            channel = getattr(provider, "channel", "") or getattr(provider, "port", "")
            baud = getattr(provider, "baudrate", "") or getattr(provider, "bitrate", "")
            if channel:
                details.append(str(channel))
            if baud:
                details.append(f"@ {baud}")
            label = QtWidgets.QListWidgetItem(f"{name} {' '.join(details)}".strip())
            self.provider_list.addItem(label)

    def _apply_touch_targets(self) -> None:
        controls = [
            getattr(self, "style_selector", None),
            getattr(self, "layout_mode_combo", None),
            getattr(self, "layout_preset_combo", None),
            getattr(self, "apply_theme_btn", None),
            getattr(self, "fullscreen_btn", None),
            getattr(self, "quick_ports_btn", None),
            getattr(self, "quick_layout_btn", None),
            getattr(self, "can_config_btn", None),
            getattr(self, "bcm_config_btn", None),
            getattr(self, "kline_config_btn", None),
        ]
        for control in controls:
            if control:
                control.setMinimumHeight(46)
                control.setMinimumWidth(180)
        if hasattr(self, "tabs"):
            self.tabs.setTabBarAutoHide(False)

    def _apply_layout_choice(self, choice: str) -> None:
        if not hasattr(self, "gauges_row"):
            return

        direction = QtWidgets.QBoxLayout.LeftToRight
        swap = False
        if choice == "Swap speed / RPM":
            swap = True
        elif choice == "Vertical stack":
            direction = QtWidgets.QBoxLayout.TopToBottom

        self.gauges_row.setDirection(direction)
        self._rebuild_gauge_order(swap)
        self._sync_layout_comboboxes(choice)

    def _rebuild_gauge_order(self, swap: bool) -> None:
        for i in reversed(range(self.gauges_row.count())):
            item = self.gauges_row.takeAt(i)
            if item.widget():
                item.widget().setParent(None)

        widgets = [self.speed_gauge, self.rpm_gauge]
        if swap:
            widgets.reverse()
        for widget in widgets:
            self.gauges_row.addWidget(widget, 1)

    def _sync_layout_comboboxes(self, choice: str) -> None:
        with QtCore.QSignalBlocker(self.layout_mode_combo):
            self.layout_mode_combo.setCurrentText(choice)
        with QtCore.QSignalBlocker(self.layout_preset_combo):
            self.layout_preset_combo.setCurrentText(choice)

    def _apply_slot_assignments(self) -> None:
        if not hasattr(self, "dashboard_grid"):
            return
        for i in reversed(range(self.dashboard_grid.count())):
            item = self.dashboard_grid.takeAt(i)
            if item.widget():
                item.widget().setParent(None)

        for slot, key in self.slot_assignments.items():
            widget = self.section_widgets.get(key)
            if not widget:
                continue
            row, col, rowspan, colspan = self.slot_positions[slot]
            self.dashboard_grid.addWidget(widget, row, col, rowspan, colspan)

        self._refresh_dropzones()

    def _apply_layout_visibility(self) -> None:
        show_assist = self.assist_toggle.isChecked()
        show_status = self.status_toggle.isChecked()
        if hasattr(self, "assist_panel"):
            self.assist_panel.setVisible(show_assist)
        if hasattr(self, "status_panel"):
            self.status_panel.setVisible(show_status)

    def _refresh_dropzones(self) -> None:
        if not hasattr(self, "drop_zones"):
            return
        title_lookup = {
            "hero": "Hero row",
            "gauges": "Gauges",
            "assist": "Assist cards",
            "status": "Status chips",
        }
        for slot, zone in self.drop_zones.items():
            key = self.slot_assignments.get(slot, "")
            label = title_lookup.get(key, "Empty")
            zone.set_assigned(label)

    def _on_tile_dropped(self, slot: str, key: str) -> None:
        if key not in self.section_widgets:
            return
        existing_slot = next((s for s, v in self.slot_assignments.items() if v == key), None)
        target_previous = self.slot_assignments.get(slot)
        if existing_slot:
            self.slot_assignments[existing_slot] = target_previous or ""
        self.slot_assignments[slot] = key
        self._apply_slot_assignments()

    def _normalize_color(self, value: str) -> str:
        value = value.strip()
        if not value:
            return "#ffffff"
        if not value.startswith("#"):
            value = f"#{value}"
        return value

    def _safe_int(self, text: str, fallback: int) -> int:
        try:
            return int(text)
        except Exception:  # noqa: BLE001
            return fallback

    def _port_summary_text(self) -> str:
        return (
            "Current: "
            f"CAN {self.current_config.can_channel or 'sim'} @ {self.current_config.can_bitrate} | "
            f"BCM {self.current_config.bcm_can_channel or self.current_config.can_channel or 'sim'} @ {self.current_config.bcm_can_bitrate} | "
            f"K-Line {self.current_config.kline_port or 'sim'} @ {self.current_config.kline_baud} | "
            f"Simulator {'on' if self.current_config.enable_simulator else 'off'}"
        )

    def _open_can_dialog(self) -> None:
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Engine CAN settings")
        form = QtWidgets.QFormLayout(dialog)

        channel_input = QtWidgets.QLineEdit(self.current_config.can_channel)
        bitrate_input = QtWidgets.QLineEdit(str(self.current_config.can_bitrate))
        form.addRow("CAN channel", channel_input)
        form.addRow("Bitrate", bitrate_input)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )

        def accept() -> None:
            self.current_config.can_channel = channel_input.text().strip()
            self.current_config.can_bitrate = self._safe_int(
                bitrate_input.text(), self.current_config.can_bitrate
            )
            self._apply_config_change("Updated CAN settings")
            dialog.accept()

        buttons.accepted.connect(accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        dialog.exec()

    def _open_bcm_dialog(self) -> None:
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("BCM CAN settings")
        form = QtWidgets.QFormLayout(dialog)

        channel_input = QtWidgets.QLineEdit(
            self.current_config.bcm_can_channel or self.current_config.can_channel
        )
        bitrate_input = QtWidgets.QLineEdit(str(self.current_config.bcm_can_bitrate))
        form.addRow("BCM channel", channel_input)
        form.addRow("Bitrate", bitrate_input)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )

        def accept() -> None:
            self.current_config.bcm_can_channel = channel_input.text().strip()
            self.current_config.bcm_can_bitrate = self._safe_int(
                bitrate_input.text(), self.current_config.bcm_can_bitrate
            )
            self._apply_config_change("Updated BCM settings")
            dialog.accept()

        buttons.accepted.connect(accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        dialog.exec()

    def _open_kline_dialog(self) -> None:
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("K-Line settings")
        layout = QtWidgets.QVBoxLayout(dialog)

        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignRight)

        port_combo = QtWidgets.QComboBox()
        port_combo.setEditable(True)
        self._populate_serial_combo(port_combo, self.current_config.kline_port)
        form.addRow("K-Line port", port_combo)

        baud_input = QtWidgets.QLineEdit(str(self.current_config.kline_baud))
        form.addRow("Baud", baud_input)

        detect_btn = QtWidgets.QPushButton("Auto-detect")

        def detect() -> None:
            detected = self.auto_detect_kline(port_combo.currentText())
            if detected:
                port_combo.setCurrentText(detected)
            else:
                QtWidgets.QMessageBox.information(
                    dialog,
                    "Auto-detect",
                    "No ELM/K-Line adapter found. Check USB connections.",
                )

        detect_btn.clicked.connect(detect)
        form.addRow("Detect", detect_btn)

        layout.addLayout(form)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )

        def accept() -> None:
            port_value = port_combo.currentData() or port_combo.currentText()
            self.current_config.kline_port = str(port_value).strip()
            self.current_config.kline_baud = self._safe_int(
                baud_input.text(), self.current_config.kline_baud
            )
            self._apply_config_change("Updated K-Line settings")
            dialog.accept()

        buttons.accepted.connect(accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()

    def _toggle_simulation_mode(self) -> None:
        self.current_config.enable_simulator = self.sim_toggle.isChecked()
        self._apply_config_change("Applied simulator toggle")

    def _apply_config_change(self, status: str) -> None:
        try:
            self.reconfigure_callback(self.current_config)
            self.hardware_status_label.setText(f"Status: {status}")
            if hasattr(self, "port_summary"):
                self.port_summary.setText(self._port_summary_text())
        except Exception as exc:  # noqa: BLE001
            self.hardware_status_label.setText(f"Status: Failed to apply: {exc}")
        self._populate_provider_list()

    def _populate_serial_combo(
        self, combo: QtWidgets.QComboBox, current: str | None = None
    ) -> None:
        combo.clear()
        labels = available_serial_labels()
        if not labels:
            combo.addItem(current or "")
            return
        for label in labels:
            combo.addItem(label, extract_device(label))
        if current:
            combo.setCurrentText(current)

    def _apply_custom_theme(self) -> None:
        name = self.theme_name_input.text().strip() or "custom"
        palette = {key: self._normalize_color(edit.text()) for key, edit in self.theme_inputs.items()}
        self.speed_gauge.setCustomStyle(palette, name)
        self.rpm_gauge.setCustomStyle(palette, name)
        if self.style_selector.findText(name) == -1:
            self.style_selector.addItem(name)
        self.style_selector.setCurrentText(name)

    def _jump_to_tab(self, widget: QtWidgets.QWidget) -> None:
        index = self.tabs.indexOf(widget)
        if index != -1:
            self.tabs.setCurrentIndex(index)

    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_btn.setText("Full screen")
        else:
            self.showFullScreen()
            self.fullscreen_btn.setText("Exit full screen")

    def _pick_color(self, field: str) -> None:
        dialog = QtWidgets.QColorDialog(self)
        dialog.setOption(QtWidgets.QColorDialog.ShowAlphaChannel, False)
        if dialog.exec():
            color = dialog.selectedColor().name()
            self.theme_inputs[field].setText(color)
