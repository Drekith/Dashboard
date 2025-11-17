from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from dashboard.state import IndicatorState
from dashboard.ui.gauge import GaugeWidget


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, pipeline):
        super().__init__()
        self.pipeline = pipeline
        self.setWindowTitle("Vivaro Cluster")
        self.setMinimumSize(1280, 720)
        self.setStyleSheet(
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
            """
        )

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

        self.nav_distance_label = QtWidgets.QLabel("A 0 ft")
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

        gauges_row = QtWidgets.QHBoxLayout()
        gauges_row.setSpacing(18)

        self.speed_gauge = GaugeWidget("Speed", "mph", 120)
        self.rpm_gauge = GaugeWidget("RPM", "rpm", 7000)
        gauges_row.addWidget(self.speed_gauge, 1)
        gauges_row.addWidget(self.rpm_gauge, 1)

        layout.addLayout(gauges_row)

        info_row = QtWidgets.QHBoxLayout()
        info_row.setSpacing(18)

        self.assist_panel = self._build_assist_panel()
        info_row.addWidget(self.assist_panel, 1)

        self.status_panel = self._build_status_panel()
        info_row.addWidget(self.status_panel, 1)

        layout.addLayout(info_row)
        self.setCentralWidget(central)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.refresh_ui)
        self.timer.start(150)

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
        self.nav_distance_label.setText(f"A {distance}" if distance else "")

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

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # noqa: N802
        self.pipeline.stop()
        super().closeEvent(event)

    def _update_chip(self, chip: QtWidgets.QWidget, text: str) -> None:
        chip.value_label.setText(text)  # type: ignore[attr-defined]

    def _on_style_changed(self, style_name: str) -> None:
        self.speed_gauge.setStyle(style_name)
        self.rpm_gauge.setStyle(style_name)
