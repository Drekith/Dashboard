from __future__ import annotations

import math

from PySide6 import QtCore, QtGui, QtWidgets


class GaugeWidget(QtWidgets.QWidget):
    """Animated circular gauge with selectable visual styles."""

    STYLES = {
        "oem": {
            "track": "#0a0e16",
            "glow": "#111a29",
            "accent": "#4fc3f7",
            "accent_alt": "#6ee7ff",
            "text": "#e8f0ff",
        },
        "neo": {
            "track": "#111827",
            "glow": "#1f2937",
            "accent": "#22d3ee",
            "accent_alt": "#a855f7",
            "text": "#e5e7eb",
        },
        "contrast": {
            "track": "#0f172a",
            "glow": "#111827",
            "accent": "#fbbf24",
            "accent_alt": "#f59e0b",
            "text": "#f8fafc",
        },
        "mono": {
            "track": "#1c1c1c",
            "glow": "#0f0f0f",
            "accent": "#9ca3af",
            "accent_alt": "#e5e7eb",
            "text": "#f3f4f6",
        },
    }

    displayValueChanged = QtCore.Signal(float)

    def __init__(self, title: str, unit: str, maximum: float, style: str = "oem") -> None:
        super().__init__()
        self.title = title
        self.unit = unit
        self.maximum = maximum
        self._value = 0.0
        self._display_value = 0.0
        self._style: dict[str, str] = {}
        self._style_name = ""

        self._anim = QtCore.QPropertyAnimation(self, b"displayValue")
        self._anim.setDuration(450)
        self._anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)

        self.setMinimumSize(260, 260)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.setStyle(style)

    def _palette(self, style_name: str | None = None) -> dict[str, str]:
        """Return a validated palette, falling back to the default."""

        if style_name and style_name in self.STYLES:
            palette = self.STYLES[style_name]
        elif self._style_name and self._style_name in self.STYLES:
            palette = self.STYLES[self._style_name]
        else:
            palette = self.STYLES["oem"]

        # Ensure required keys exist to avoid blank paints when a custom style
        # was partially provided.
        required_keys = {"track", "glow", "accent", "accent_alt", "text"}
        if not required_keys.issubset(palette):
            return self.STYLES["oem"]
        return palette

    def setStyle(self, style_name: str) -> None:  # noqa: N802
        style = self._palette(style_name)
        self._style = style
        self._style_name = style_name if style_name in self.STYLES else "oem"
        self.update()

    def setCustomStyle(self, palette: dict[str, str], name: str = "custom") -> None:  # noqa: N802
        """Apply a custom palette to the gauge.

        The palette must include the keys: track, glow, accent, accent_alt, text.
        """

        required_keys = {"track", "glow", "accent", "accent_alt", "text"}
        if not required_keys.issubset(palette):
            # Merge any provided keys with a fallback to keep gauges visible.
            merged = {**self.STYLES["oem"], **palette}
            palette = {key: merged[key] for key in required_keys}

        # Register so style selectors can reference the custom entry.
        self.STYLES[name] = palette
        self._style_name = name
        self._style = palette
        self.update()

    def setValue(self, value: float) -> None:  # noqa: N802
        clamped = max(0.0, min(self.maximum, value))
        if math.isclose(clamped, self._display_value, abs_tol=0.2):
            self._display_value = clamped
            self._value = clamped
            self.update()
            return

        self._value = clamped
        self._anim.stop()
        self._anim.setStartValue(self._display_value)
        self._anim.setEndValue(clamped)
        self._anim.start()

    def getDisplayValue(self) -> float:  # noqa: N802
        return self._display_value

    def setDisplayValue(self, value: float) -> None:  # noqa: N802
        self._display_value = value
        self.displayValueChanged.emit(value)
        self.update()

    displayValue = QtCore.Property(float, getDisplayValue, setDisplayValue)  # type: ignore[assignment]

    def paintEvent(self, _: QtGui.QPaintEvent) -> None:  # noqa: N802
        painter = QtGui.QPainter()
        if not painter.begin(self):
            return

        try:
            hints = QtGui.QPainter.Antialiasing | QtGui.QPainter.TextAntialiasing
            if hasattr(QtGui.QPainter, "SmoothPixmapTransform"):
                hints |= QtGui.QPainter.SmoothPixmapTransform
            painter.setRenderHints(hints)

            rect = self.rect().adjusted(22, 22, -22, -22)
            radius = min(rect.width(), rect.height()) / 2
            center = rect.center()

            start_angle = 135
            span_angle = 270
            pen_width = 18

            # background track
            palette = self._palette()

            ring_brush = QtGui.QRadialGradient(center, radius)
            ring_brush.setColorAt(0, QtGui.QColor(palette["glow"]).lighter(120))
            ring_brush.setColorAt(1, QtGui.QColor(palette["track"]))

            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(ring_brush)
            painter.drawEllipse(QtCore.QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2))

            track_pen = QtGui.QPen(QtGui.QColor(palette["track"]).lighter(105))
            track_pen.setWidth(pen_width)
            track_pen.setCapStyle(QtCore.Qt.RoundCap)
            painter.setPen(track_pen)
            painter.drawArc(
                QtCore.QRectF(
                    center.x() - radius, center.y() - radius, radius * 2, radius * 2
                ),
                start_angle * 16,
                -span_angle * 16,
            )

            # glow layer
            glow_pen = QtGui.QPen(QtGui.QColor(palette["glow"]).darker(110))
            glow_pen.setWidth(pen_width + 10)
            glow_pen.setCapStyle(QtCore.Qt.RoundCap)
            painter.setPen(glow_pen)
            painter.drawArc(
                QtCore.QRectF(
                    center.x() - radius + 8,
                    center.y() - radius + 8,
                    (radius - 8) * 2,
                    (radius - 8) * 2,
                ),
                start_angle * 16,
                -span_angle * 16,
            )

            # inner halo to lift the dial off the background
            halo_brush = QtGui.QRadialGradient(center, radius * 0.65)
            halo_brush.setColorAt(0.0, QtGui.QColor(palette["glow"]).lighter(140))
            halo_brush.setColorAt(1.0, QtGui.QColor(palette["track"]).darker(140))
            painter.setBrush(halo_brush)
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(
                QtCore.QRectF(
                    center.x() - radius * 0.68,
                    center.y() - radius * 0.68,
                    radius * 1.36,
                    radius * 1.36,
                )
            )

            # value arc
            ratio = (self._display_value / self.maximum) if self.maximum else 0
            value_angle = span_angle * ratio
            gradient = QtGui.QConicalGradient(center, -start_angle)
            gradient.setColorAt(0.0, QtGui.QColor(palette["accent"]))
            gradient.setColorAt(0.5, QtGui.QColor(palette["accent_alt"]))
            gradient.setColorAt(1.0, QtGui.QColor(palette["accent"]))
            value_pen = QtGui.QPen(QtGui.QBrush(gradient), pen_width)
            value_pen.setCapStyle(QtCore.Qt.RoundCap)
            painter.setPen(value_pen)
            painter.drawArc(
                QtCore.QRectF(
                    center.x() - radius, center.y() - radius, radius * 2, radius * 2
                ),
                start_angle * 16,
                -value_angle * 16,
            )

            # tick marks
            painter.save()
            painter.translate(center)
            tick_pen = QtGui.QPen(QtGui.QColor(palette["accent_alt"]))
            tick_pen.setWidth(2)
            painter.setPen(tick_pen)
            ticks = 8
            for i in range(ticks + 1):
                angle = math.radians(start_angle + (span_angle / ticks) * i)
                inner = QtCore.QPointF(
                    math.cos(angle) * (radius - pen_width * 1.5),
                    math.sin(angle) * (radius - pen_width * 1.5),
                )
                outer = QtCore.QPointF(
                    math.cos(angle) * (radius - pen_width * 0.5),
                    math.sin(angle) * (radius - pen_width * 0.5),
                )
                painter.drawLine(inner, outer)

            label_font = QtGui.QFont("Segoe UI", 11, QtGui.QFont.DemiBold)
            painter.setFont(label_font)
            painter.setPen(QtGui.QColor(palette["text"]).lighter(115))
            label_radius = radius - pen_width * 2.6
            for i in range(ticks + 1):
                angle = math.radians(start_angle + (span_angle / ticks) * i)
                pos = QtCore.QPointF(
                    math.cos(angle) * label_radius,
                    math.sin(angle) * label_radius,
                )
                value = int(self.maximum / ticks * i)
                painter.save()
                painter.translate(pos)
                painter.rotate((math.degrees(angle) + 90))
                painter.drawText(
                    QtCore.QRectF(-16, -10, 32, 20),
                    QtCore.Qt.AlignCenter,
                    f"{value}",
                )
                painter.restore()
            painter.restore()

            # value text
            angle_deg = start_angle - value_angle
            angle_rad = math.radians(angle_deg)
            indicator_point = QtCore.QPointF(
                center.x() + math.cos(angle_rad) * (radius - pen_width * 0.7),
                center.y() + math.sin(angle_rad) * (radius - pen_width * 0.7),
            )
            indicator_pen = QtGui.QPen(QtGui.QColor(palette["accent_alt"]))
            indicator_pen.setWidth(6)
            painter.setPen(indicator_pen)
            painter.drawPoint(indicator_point)

            inner_ring_pen = QtGui.QPen(QtGui.QColor(palette["glow"]).lighter(130))
            inner_ring_pen.setWidth(3)
            painter.setPen(inner_ring_pen)
            painter.setBrush(QtGui.QColor(palette["track"]).darker(140))
            painter.drawEllipse(center, radius * 0.32, radius * 0.32)

            painter.setPen(QtGui.QColor(palette["text"]))
            value_font = QtGui.QFont("Segoe UI", 42, QtGui.QFont.Bold)
            painter.setFont(value_font)
            painter.drawText(
                self.rect(),
                QtCore.Qt.AlignCenter,
                f"{self._display_value:,.0f}\n{self.unit.upper()}",
            )

            # title text
            title_font = QtGui.QFont("Segoe UI", 16, QtGui.QFont.Medium)
            painter.setFont(title_font)
            painter.drawText(
                QtCore.QRectF(self.rect()).adjusted(0, 12, 0, 0),
                QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop,
                self.title,
            )
        finally:
            painter.end()

