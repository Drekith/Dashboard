from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from dashboard.state import IndicatorState


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, pipeline):
        super().__init__()
        self.pipeline = pipeline
        self.setWindowTitle("Vivaro Cluster")
        self.setMinimumSize(1200, 600)
        self.setStyleSheet(
            """
            QWidget { background-color: #0d1117; color: #e5e7eb; }
            QLabel { font-family: 'Segoe UI', sans-serif; }
            QLabel[role="title"] { font-size: 42px; font-weight: 600; }
            QLabel[role="subtitle"] { font-size: 24px; color: #9ca3af; }
            QLabel[role="value"] { font-size: 32px; font-weight: 600; }
            QLabel[role="label"] { font-size: 16px; color: #9ca3af; }
            .panel { background: #111827; border-radius: 18px; padding: 18px; }
            """
        )

        central = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(central)
        layout.setSpacing(24)
        layout.setContentsMargins(24, 24, 24, 24)

        self.cluster_panel = self._build_cluster_panel()
        self.assist_panel = self._build_assist_panel()

        layout.addWidget(self.cluster_panel, 2)
        layout.addWidget(self.assist_panel, 1)
        self.setCentralWidget(central)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.refresh_ui)
        self.timer.start(200)

    def _build_cluster_panel(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout(panel)
        layout.setHorizontalSpacing(32)
        layout.setVerticalSpacing(8)

        self.heading_label = QtWidgets.QLabel("⬆")
        self.heading_label.setProperty("role", "title")
        self.heading_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        layout.addWidget(self.heading_label, 0, 0, 1, 1)

        self.nav_distance_label = QtWidgets.QLabel("A 200 ft")
        self.nav_distance_label.setProperty("role", "subtitle")
        layout.addWidget(self.nav_distance_label, 0, 1, 1, 1)

        self.speed_label = QtWidgets.QLabel("0")
        self.speed_label.setProperty("role", "title")
        self.speed_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.speed_label, 1, 0, 1, 2)

        mph_label = QtWidgets.QLabel("MPH")
        mph_label.setProperty("role", "subtitle")
        mph_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(mph_label, 2, 0, 1, 2)

        self.battery_label = QtWidgets.QLabel("0%")
        self.battery_label.setProperty("role", "subtitle")
        self.battery_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.battery_label, 3, 0, 1, 1)

        self.rpm_label = QtWidgets.QLabel("RPM x1000")
        self.rpm_label.setProperty("role", "subtitle")
        layout.addWidget(self.rpm_label, 3, 1, 1, 1)

        self.indicator_label = QtWidgets.QLabel("")
        self.indicator_label.setProperty("role", "subtitle")
        layout.addWidget(self.indicator_label, 4, 0, 1, 2)

        return panel

    def _build_assist_panel(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout(panel)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(18)

        self.nav_panel, self.nav_body = self._make_card("Navig", "South in 200 ft")
        layout.addWidget(self.nav_panel, 0, 0, 1, 2)

        self.radio_panel, self.radio_body = self._make_card("Radio", "")
        layout.addWidget(self.radio_panel, 1, 0, 1, 1)

        self.vehicle_panel, self.vehicle_body = self._make_card("Vehicle", "72°")
        layout.addWidget(self.vehicle_panel, 1, 1, 1, 1)

        self.drive_panel, self.drive_body = self._make_card("Drive Mode", "ECO")
        layout.addWidget(self.drive_panel, 2, 0, 1, 2)

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

    def refresh_ui(self) -> None:
        state = self.pipeline.snapshot()
        self.speed_label.setText(f"{state.speed_mph:.0f}")
        self.battery_label.setText(f"{state.battery_level}%")
        self.rpm_label.setText(f"RPM x1000  {state.rpm/1000:.1f}")
        heading_symbol = {"L": "⬅", "R": "➡"}.get(state.formatted_heading(), "⬆")
        self.heading_label.setText(heading_symbol)
        distance = state.formatted_nav_distance()
        self.nav_distance_label.setText(f"A {distance}" if distance else "")

        indicator_text = {
            IndicatorState.OFF: "",
            IndicatorState.LEFT: "Left indicator",
            IndicatorState.RIGHT: "Right indicator",
            IndicatorState.HAZARD: "Hazard lights",
        }[state.indicator]
        if state.door_open:
            indicator_text = "Door open" if not indicator_text else f"{indicator_text} / Door open"
        self.indicator_label.setText(indicator_text)

        self.nav_body.setText(f"{heading_symbol} {distance}")
        self.radio_body.setText(state.radio_station)
        self.vehicle_body.setText(f"{state.ambient_temp_f:.0f}°F")
        self.drive_body.setText(state.drive_mode)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # noqa: N802
        self.pipeline.stop()
        super().closeEvent(event)
