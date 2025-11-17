from __future__ import annotations

import textwrap

from PySide6 import QtCore, QtGui, QtWidgets

from dashboard.services.data_pipeline import DataPipeline
from dashboard.state import IndicatorState
from dashboard.ui.gauge import GaugeWidget


GLOBAL_STYLES = textwrap.dedent(
    """
    QWidget { background-color: #05070f; color: #e5e7eb; }
    QLabel { font-family: 'Segoe UI', sans-serif; }
    QLabel[role="title"] { font-size: 32px; font-weight: 700; letter-spacing: 0.5px; }
    QLabel[role="subtitle"] { font-size: 20px; color: #cbd5e1; }
    QLabel[role="value"] { font-size: 24px; font-weight: 600; }
    QLabel[role="label"] { font-size: 14px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1.2px; }
    .panel { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0b1220, stop:1 #0f172a); border: 1px solid #1f2937; border-radius: 18px; padding: 18px; }
    .chip { background: rgba(148, 163, 184, 0.14); border-radius: 12px; padding: 8px 12px; }
    QComboBox { background: #0f172a; padding: 8px 12px; border: 1px solid #1f2937; border-radius: 12px; color: #e2e8f0; }
    QComboBox QAbstractItemView { background: #0f172a; selection-background-color: #1f2937; }
    QListWidget[class="panel"] { border: 1px solid #1f2937; border-radius: 12px; background: #0b1220; }
    QListWidget[class="panel"]::item { padding: 10px; }
    QPushButton { background: #1f2937; border: 1px solid #334155; border-radius: 10px; padding: 10px 14px; color: #e2e8f0; }
    QPushButton:hover { background: #273548; }
    QLineEdit { background: #0f172a; border: 1px solid #1f2937; border-radius: 10px; padding: 8px 10px; color: #e2e8f0; }
    """
)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, pipeline: DataPipeline):
        super().__init__()
        self.pipeline = pipeline
        self.setWindowTitle("Vivaro Cluster")
        self.setMinimumSize(1280, 720)
        self.setStyleSheet(GLOBAL_STYLES)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setTabPosition(QtWidgets.QTabWidget.North)
        self.tabs.setDocumentMode(True)

        self.dashboard_tab = self._build_dashboard_tab()
        self.settings_tab = self._build_settings_tab()
        self.theme_tab = self._build_theme_editor_tab()
        self.layout_tab = self._build_layout_editor_tab()

        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.settings_tab, "Settings")
        self.tabs.addTab(self.theme_tab, "Theme Editor")
        self.tabs.addTab(self.layout_tab, "Layout Editor")

        self.setCentralWidget(self.tabs)

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
        self.style_selector.addItems(["neo", "contrast", "mono"])
        self.style_selector.currentTextChanged.connect(self._on_style_changed)
        header_row.addWidget(self.style_selector)

        layout.addLayout(header_row)

        self.gauges_row = QtWidgets.QHBoxLayout()
        self.gauges_row.setSpacing(18)
        self.gauges_row.setDirection(QtWidgets.QBoxLayout.LeftToRight)

        self.speed_gauge = GaugeWidget("Speed", "mph", 120)
        self.rpm_gauge = GaugeWidget("RPM", "rpm", 7000)
        self.gauges_row.addWidget(self.speed_gauge, 1)
        self.gauges_row.addWidget(self.rpm_gauge, 1)

        layout.addLayout(self.gauges_row)

        info_row = QtWidgets.QHBoxLayout()
        info_row.setSpacing(18)

        self.assist_panel = self._build_assist_panel()
        info_row.addWidget(self.assist_panel, 1)

        self.status_panel = self._build_status_panel()
        info_row.addWidget(self.status_panel, 1)

        layout.addLayout(info_row)
        return central

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
            line_edit = QtWidgets.QLineEdit(GaugeWidget.STYLES["neo"][key])
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
        for provider in self.pipeline.providers:
            name = provider.__class__.__name__
            label = QtWidgets.QListWidgetItem(name)
            self.provider_list.addItem(label)

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

    def _apply_layout_visibility(self) -> None:
        show_assist = self.assist_toggle.isChecked()
        show_status = self.status_toggle.isChecked()
        if hasattr(self, "assist_panel"):
            self.assist_panel.setVisible(show_assist)
        if hasattr(self, "status_panel"):
            self.status_panel.setVisible(show_status)

    def _normalize_color(self, value: str) -> str:
        value = value.strip()
        if not value:
            return "#ffffff"
        if not value.startswith("#"):
            value = f"#{value}"
        return value

    def _apply_custom_theme(self) -> None:
        name = self.theme_name_input.text().strip() or "custom"
        palette = {key: self._normalize_color(edit.text()) for key, edit in self.theme_inputs.items()}
        self.speed_gauge.setCustomStyle(palette, name)
        self.rpm_gauge.setCustomStyle(palette, name)
        if self.style_selector.findText(name) == -1:
            self.style_selector.addItem(name)
        self.style_selector.setCurrentText(name)

    def _pick_color(self, field: str) -> None:
        dialog = QtWidgets.QColorDialog(self)
        dialog.setOption(QtWidgets.QColorDialog.ShowAlphaChannel, False)
        if dialog.exec():
            color = dialog.selectedColor().name()
            self.theme_inputs[field].setText(color)
