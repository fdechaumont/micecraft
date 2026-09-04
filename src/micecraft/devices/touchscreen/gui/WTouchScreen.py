from typing import Any, Callable
import math

from PyQt6.QtWidgets import QApplication, QMenu, QWidget, QInputDialog
from PyQt6.QtGui import (
    QAction,
    QCloseEvent,
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QPaintEvent,
    QPen,
)
from PyQt6.QtCore import (
    QLine,
    QLineF,
    QMargins,
    QPointF,
    QRect,
    QSize,
    Qt,
    QTimer,
)

from micecraft.soft.device_event.DeviceEvent import DeviceEvent
from micecraft.devices.touchscreen.TouchScreen2 import TouchScreen2
from micecraft.devices.touchscreen.inPy.ts_img_manager import TSImage
from micecraft.soft.gui.VisualDeviceAlarmStatus import VisualDeviceAlarmStatus


class WScreenTouch:
    """A small widget to show a touch point indicator at a given position."""

    def __init__(
        self,
        touch_point: QPointF,
        on_symbol: bool,
        update_callback: Callable,
        visible_time: int = 3,
        fading_time: int = 2,
        size: int = 3,
    ):
        """Initialize the touch point indicator.

        Parameters:
        -----------
        touch_point: QPointF
            The position (x, y) of the touch point on the screen.
        update_callback: Callable
            A callback function to call when the indicator needs to be updated
            (e.g. removed after the timer ends).
        visible_time: int
            The time in seconds for which the indicator should be visible
            before being removed.
        size: int
            The size in pixels of the cross-hair lines to indicate the touch
            point.
        """
        self.touch_point: QPointF = touch_point
        """Position (x, y) on the widget displayed area."""
        self.on_symbol: bool = on_symbol
        self.show: bool = True
        self.size: int = size
        self.visible_time: int = visible_time * 1_000
        """Time in milliseconds for which the indicator should be visible."""
        self.fading_time: int = fading_time * 1_000
        """Time in milliseconds for which the indicator should fade out
        (included in the visible time)."""
        self.update_callback: Callable = update_callback

        self.timer: QTimer | None = None

    def get_rect(self) -> QRect:
        """Get the rectangle area covered by this indicator, based on its
        position and size."""
        return QRect(
            int(self.touch_point.x() - self.size),
            int(self.touch_point.y() - self.size),
            int(self.size * 2),
            int(self.size * 2),
        )

    def __eq__(self, other):
        if not isinstance(other, WScreenTouch):
            return False
        return self.touch_point == other.touch_point

    def start_timer(self):
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.end_timer)
        self.timer.start(self.visible_time)

    def end_timer(self):
        if self.timer is not None:
            self.timer.stop()
        self.show = False
        self.update_callback()

    def get_alpha(self) -> int:
        """Get the current alpha value for the indicator, based on the
        remaining time before it disappears."""
        if self.timer is None or not self.timer.isActive():
            return 0
        rt = self.timer.remainingTime()
        if rt < self.fading_time:
            return int(255 * rt / self.fading_time)
        else:
            return 255


class WTouchScreen(QWidget):
    """
    Visual widget for a TouchScreen device. All calculations are based on the
    horizontal orientation. The rotation is applied during the `paintEvent`
    method by swapping x and y coordinates.

    - Renders a cross-hair touch indicator at the last touched position.
    - Shows an enabled / disabled status dot and overlay.
    - Right-click menu: simulate left / right touch, set an image on an area.
    """

    SCREEN_SIZE = QSize(1920, 1080)
    """(width, height) in *px* for horizontal orientation."""
    WIDGET_SIZE = QSize(120, 90)
    """(width, height) in *px* for horizontal orientation."""
    WIDGET_TEXT_HEIGHT = 18
    """Margin in *px* between the widget border and the text."""
    WIDGET_ALARM_WIDTH = 28
    """Width in *px* of the alarm status indicator area."""
    WIDGET_MARGIN = 6
    """Margin in *px* between every elements."""
    IMAGE_RECT = QRect(-16, -16, 33, 33)
    """(x, y, width, height) in *px* for the image rect centered on (0,0)."""

    BG_COLOR = QColor(220, 220, 220)
    CONTOUR_COLOR = QColor(94, 94, 94)
    LIGHT_COLOR = QColor(244, 244, 244)
    DARK_COLOR = QColor(33, 33, 33)
    TOUCH_COLOR = [QColor(255, 133, 194), QColor(33, 194, 33)]  # False, True
    CALIBRATION_COLOR = QColor(0, 194, 0)

    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        angle: int = 0,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.angle = angle
        ww = WTouchScreen.WIDGET_SIZE.width()
        wh = WTouchScreen.WIDGET_SIZE.height()

        self.max_dim = max(ww, wh)

        rect = QRect(
            int(x * 200 + 100) - self.max_dim // 2,
            int(y * 200 + 100) - self.max_dim // 2,
            self.max_dim,
            self.max_dim,
        )

        self.setGeometry(rect)
        self.touchscreen = None
        self.name = "WTS"
        self.visualDeviceAlarmStatus = VisualDeviceAlarmStatus()
        self.indicators: list[WScreenTouch] = []
        self.show_calibration = False

    def get_element_rect(
        self,
        element: str,
    ) -> QRect:
        """Get the rectangle for a given element of the widget, with an
        optional transform to apply the block wall rotation.

        Possible values for element:
        - "widget"  : the entire widget
        - "inner"   : the inner area of the widget (without margins)
        - "name"    : the area displaying the widget's name
        - "alarm"   : the area displaying the alarm status
        - "display" : the display area
        """
        alarm_w = WTouchScreen.WIDGET_ALARM_WIDTH
        text_h = WTouchScreen.WIDGET_TEXT_HEIGHT
        margin = WTouchScreen.WIDGET_MARGIN

        widget_rect = QRect(
            self.max_dim // 2 - WTouchScreen.WIDGET_SIZE.width() // 2,
            self.max_dim // 2 - WTouchScreen.WIDGET_SIZE.height() // 2,
            WTouchScreen.WIDGET_SIZE.width(),
            WTouchScreen.WIDGET_SIZE.height(),
        )
        inner_rect = widget_rect.marginsRemoved(
            QMargins(margin, margin, margin, margin)
        )

        match element:
            case "widget":
                rect = widget_rect
            case "inner":
                rect = inner_rect
            case "name":
                rect = QRect(
                    inner_rect.x() + alarm_w + margin,
                    inner_rect.y(),
                    inner_rect.width() - alarm_w - margin,
                    text_h,
                )
            case "display":
                rect = QRect(
                    inner_rect.x(),
                    inner_rect.y() + text_h + margin,
                    inner_rect.width(),
                    inner_rect.height() - text_h - margin,
                )
            case "alarm":
                rect = QRect(
                    inner_rect.x(),
                    inner_rect.y(),
                    alarm_w,
                    text_h,
                )
            case _:
                raise ValueError(f"Invalid element value: {element}")

        return rect

    def get_touch_cross(
        self,
        indicator: WScreenTouch,
    ) -> tuple[QLineF, QLineF]:
        """Get the horizontal and vertical lines to draw for a given touch
        point indicator, based on its position and the widget's block wall
        orientation."""

        cross_rect = indicator.get_rect()
        cross_center = cross_rect.center().toPointF()

        hline = QLineF(-indicator.size, 0, indicator.size, 0)
        vline = QLineF(0, -indicator.size, 0, indicator.size)

        hline.translate(cross_center)
        vline.translate(cross_center)

        return hline, vline

    def setName(self, name: str):
        self.name = name
        self.update()

    def bindToTouchScreen(self, ts: TouchScreen2):
        """Bind this widget to a TouchScreen device instance or to a
        VirtualTouchScreen instance for testing."""
        if self.touchscreen is not None:
            self.touchscreen.removeDeviceListener(
                self.widget_touchscreen_listener
            )

        self.touchscreen = ts
        self.name = ts.name
        ts.addDeviceListener(self.widget_touchscreen_listener)
        self.update()

    def get_current_display(self) -> list[dict[str, Any]]:
        """Return the active display list from the bound touchscreen."""
        if self.touchscreen is not None:
            return self.touchscreen.getCurrentImageList()
        return []

    # ================ Device Listener ================

    def widget_touchscreen_listener(self, event: DeviceEvent):
        if self.touchscreen is None:
            return

        desc = event.description
        point = None
        on_symbol = False

        if "symbol xy touched" in desc:
            # data = (name, id, x, y, xf, yf, xr, yr)
            xr = event.data[6]  # type: ignore
            yr = event.data[7]  # type: ignore
            point = QPointF(xr, yr)
            on_symbol = True

        if "missed" in desc:
            # data = (xf, yf, xr, yr)
            xr = event.data[2]  # type: ignore
            yr = event.data[3]  # type: ignore
            point = QPointF(xr, yr)

        if point is not None:
            wscreen = self.get_element_rect("display")
            wpoint = QPointF(
                point.x() * wscreen.width() + wscreen.x(),
                point.y() * wscreen.height() + wscreen.y(),
            )
            indicator = WScreenTouch(wpoint, on_symbol, self.update)
            if indicator in self.indicators:
                self.indicators.remove(indicator)
            self.indicators.append(indicator)

        self.update()

    # ================ PAINT ================

    def draw_text(
        self,
        p: QPainter,
        rect: QRect,
        txt: str,
    ):
        """Draw text in the given rectangle (size is adapted and rotated if
        vertical orientation)."""
        p.save()

        cur_font: QFont = p.font()
        family = cur_font.family() or ""
        bold = cur_font.bold()

        # start from the painter's point size if available, otherwise use 16
        try:
            max_size = int(cur_font.pointSize())
        except Exception:
            max_size = 16

        if max_size <= 0:
            max_size = 16

        min_size = 6
        pad = 4

        best = min_size
        low = min_size
        high = max_size

        while low <= high:
            mid = (low + high) // 2
            f = QFont(family, mid)
            f.setBold(bold)
            fm = QFontMetrics(f)
            br = fm.boundingRect(txt)
            if (
                br.width() <= rect.width() - pad
                and br.height() <= rect.height() - pad
            ):
                best = mid
                low = mid + 1
            else:
                high = mid - 1

        fit_font = QFont(family, best)
        fit_font.setBold(bold)
        p.setFont(fit_font)
        p.drawText(QRect(rect), Qt.AlignmentFlag.AlignCenter, txt)
        p.restore()

    def paintEvent(self, event: QPaintEvent):  # type: ignore[override]
        super().paintEvent(event)

        # timers must be created here for thread affinity reasons
        for indicator in self.indicators:
            if indicator.timer is None:
                indicator.start_timer()

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        p.translate(self.width() / 2, self.height() / 2)
        p.rotate(self.angle)
        p.translate(-self.width() / 2, -self.height() / 2)

        # widget background
        p.fillRect(
            self.get_element_rect("widget"),
            WTouchScreen.BG_COLOR,
        )

        # widget contour
        p.setPen(QPen(WTouchScreen.CONTOUR_COLOR, 2))
        p.drawRect(
            self.get_element_rect("widget").marginsRemoved(
                QMargins(1, 1, 1, 1)
            )
        )

        # screen background
        p.fillRect(
            self.get_element_rect("display"),
            WTouchScreen.DARK_COLOR,
        )

        # display images
        for img in self.get_current_display():
            if img["type"] not in ["xy_image", "xy_stripes"]:
                continue

            if img["type"] == "xy_image":
                # image
                img_id = img["id"]
                img_cx = img["centerX"]
                img_cy = img["centerY"]
                img_rot = img.get("rotation", 0)

                screen_rect = self.get_element_rect("display")
                if img["unit"] == "ratio":
                    img_cx = img_cx * screen_rect.width()
                    img_cy = img_cy * screen_rect.height()

                name = TSImage.get_unicode_from_id(img_id)
                if img_id == TSImage.LIGHT.value:
                    img_clr = WTouchScreen.LIGHT_COLOR
                    pen_clr = WTouchScreen.DARK_COLOR
                else:
                    img_clr = WTouchScreen.DARK_COLOR
                    pen_clr = WTouchScreen.LIGHT_COLOR

                cx_px = int(screen_rect.x() + img_cx)
                cy_px = int(screen_rect.y() + img_cy)

                p.save()
                p.translate(cx_px, cy_px)
                p.rotate(img_rot)
                p.setPen(WTouchScreen.CONTOUR_COLOR)
                p.drawRect(self.IMAGE_RECT)
                p.fillRect(self.IMAGE_RECT, img_clr)
                p.setPen(pen_clr)
                font = QFont("Calibri", 16)
                font.setBold(True)
                p.setFont(font)
                self.draw_text(p, self.IMAGE_RECT, name)
                p.restore()

            if img["type"] == "xy_stripes":
                # stripes: position relative, scale and rotation applied
                stripe_angle = img.get("stripe_angle", 0)
                thickness1 = img.get("thickness1", 4)
                thickness2 = img.get("thickness2", 2)
                color1 = QColor(*img.get("color1", (200, 200, 200)))
                color2 = QColor(*img.get("color2", (100, 100, 100)))
                unit = img.get("unit", "ratio")
                img_rot = img.get("rotation", 0)
                img_scale = img.get("scale", 1)
                img_cx = img.get("centerX", 0.5)
                img_cy = img.get("centerY", 0.5)

                screen_rect = self.get_element_rect("display")
                if unit == "ratio":
                    img_cx = img_cx * screen_rect.width()
                    img_cy = img_cy * screen_rect.height()

                cx_px = int(screen_rect.x() + img_cx)
                cy_px = int(screen_rect.y() + img_cy)

                base_w = WTouchScreen.IMAGE_RECT.width()
                base_h = WTouchScreen.IMAGE_RECT.height()
                w = max(1, int(base_w * img_scale))
                h = max(1, int(base_h * img_scale))

                p.save()
                p.translate(cx_px, cy_px)
                p.rotate(img_rot)
                target_rect = QRect(-w // 2, -h // 2, w, h)
                # base fill
                p.fillRect(target_rect, color1)
                # clip to target rect so stripes don't overflow
                p.setClipRect(target_rect)
                p.setPen(QPen(color2, thickness2))
                p.rotate(stripe_angle)
                # draw stripes across an extended area
                ext = int(math.hypot(w, h) // 2) + max(w, h)
                spacing = max(1, thickness1 + thickness2)
                for i in range(-ext, ext + spacing, spacing):
                    x = i
                    p.drawLine(x, -ext, x, ext)
                p.restore()

        if self.touchscreen is not None and not self.touchscreen.enabled:
            # display DISABLED
            p.setPen(WTouchScreen.BG_COLOR.darker(200))
            font = QFont("Calibri", 13)
            font.setBold(False)
            p.setFont(font)
            self.draw_text(p, self.get_element_rect("display"), "DISABLED")

        # calibration overlay
        if self.show_calibration:
            p.setPen(QPen(WTouchScreen.CALIBRATION_COLOR, 2))
            contour_rect = self.get_element_rect("display")
            p.drawRect(contour_rect)
            dx = contour_rect.width() // 2
            dy = contour_rect.height() // 2
            top_bottom = QLine(
                contour_rect.topLeft(), contour_rect.bottomLeft()
            ).translated(dx, 0)
            left_right = QLine(
                contour_rect.topLeft(), contour_rect.topRight()
            ).translated(0, dy)
            p.drawLine(top_bottom)
            p.drawLine(left_right)

        # display touch indicators
        all_indicators = self.indicators.copy()
        for indicator in all_indicators:

            if not indicator.show:
                self.indicators.remove(indicator)
                continue

            hline, vline = self.get_touch_cross(indicator)
            if indicator.on_symbol:
                touch_color = WTouchScreen.TOUCH_COLOR[1]
            else:
                touch_color = WTouchScreen.TOUCH_COLOR[0]
            touch_color.setAlpha(indicator.get_alpha())
            p.save()
            p.setPen(QPen(touch_color, 2))
            p.translate(1, 1)  # correct pen width
            p.drawLine(hline)
            p.drawLine(vline)
            p.restore()

        # name
        name_clr = WTouchScreen.BG_COLOR.darker(200)
        name_clr.setAlpha(100)
        p.setPen(name_clr)
        font_name = QFont("Calibri", 16)
        font_name.setBold(True)
        p.setFont(font_name)
        self.draw_text(p, self.get_element_rect("name"), self.name)

        # alarm
        alarm_rect = self.get_element_rect("alarm")
        dot_size = 7
        alarm_margin = 3
        ellipse_rect = QRect(
            alarm_rect.x() + alarm_margin,
            alarm_rect.y() + alarm_rect.height() // 2 - dot_size // 2,
            dot_size,
            dot_size,
        )
        text_rect = QRect(
            alarm_rect.x() + dot_size + 2 * alarm_margin,
            alarm_rect.y(),
            alarm_rect.width() - dot_size - 2 * alarm_margin,
            alarm_rect.height(),
        )
        if isinstance(self.touchscreen, TouchScreen2):
            self.visualDeviceAlarmStatus.draw(
                p,
                self.touchscreen,
                ellipseRect=ellipse_rect,
                textRect=text_rect,
            )

        p.end()

    # ================ MENU ================

    def contextMenuEvent(self, event):  # type: ignore[override]
        menu = QMenu(self)

        actions: dict[QAction, tuple[Callable, tuple]] = {}

        # title
        # ----------------
        title = QAction("TouchScreen Actions", menu)
        title.setDisabled(True)
        menu.addAction(title)
        menu.addSeparator()

        # display and clear images
        # ----------------
        display_left = QMenu("Display on left", menu)
        menu.addMenu(display_left)
        display_right = QMenu("Display on right", menu)
        menu.addMenu(display_right)
        action = QAction("Clear Images", menu)
        menu.addAction(action)
        actions[action] = (self.clear_all_images, ())

        other_images_left = QMenu("Other Images", display_left)
        display_left.addMenu(other_images_left)
        other_images_right = QMenu("Other Images", display_right)
        display_right.addMenu(other_images_right)

        main_images = [
            TSImage.DARK,
            TSImage.LIGHT,
            TSImage.PLANE,
            TSImage.FLOWER,
            TSImage.TRUE,
            TSImage.FALSE,
        ]
        for member in TSImage._member_map_.values():
            name = str(member)
            id = member.value
            if member in main_images:
                action = QAction(name, display_left)
                display_left.addAction(action)
                actions[action] = (self.display_image, (id, 0.25))

                action = QAction(name, display_right)
                display_right.addAction(action)
                actions[action] = (self.display_image, (id, 0.75))
            else:
                action = QAction(name, other_images_left)
                other_images_left.addAction(action)
                actions[action] = (self.display_image, (id, 0.25))

                action = QAction(name, other_images_right)
                other_images_right.addAction(action)
                actions[action] = (self.display_image, (id, 0.75))

        # mode (mouse, rat, normal)
        # ----------------
        mode_menu = QMenu("Set mode", menu)
        menu.addMenu(mode_menu)
        normal_mode = QAction("Normal", menu)
        mode_menu.addAction(normal_mode)
        actions[normal_mode] = (self.set_mode, ("normal",))
        mouse_mode = QAction("Mouse", menu)
        mode_menu.addAction(mouse_mode)
        actions[mouse_mode] = (self.set_mode, ("mouse",))
        rat_mode = QAction("Rat", menu)
        mode_menu.addAction(rat_mode)
        actions[rat_mode] = (self.set_mode, ("rat",))

        # touch a displayed image
        # ----------------
        user_touch = QMenu("Touch image", menu)
        menu.addMenu(user_touch)
        for img in self.get_current_display():
            name = TSImage.get_name_from_id(img["id"])
            action = QAction(name, user_touch)
            user_touch.addAction(action)
            actions[action] = (self.user_touch, (img,))

        # calibration
        # ----------------
        action = QAction("Toggle Calibration", menu)
        menu.addAction(action)
        actions[action] = (self.toggle_calibration, ())

        # image size
        # ----------------
        action = QAction("Set Image Size", menu)
        menu.addAction(action)
        actions[action] = (self.ask_image_size, ())

        chosen = menu.exec(self.mapToGlobal(event.pos()))

        if chosen is None:
            print(
                "No action as there is no hardware device bound to this component"
            )
            return

        actions[chosen][0](*actions[chosen][1])

    def display_image(
        self,
        id: int,
        cx: float = 0.5,
        cy: float = 0.5,
        unit: str = "ratio",
    ):
        """Set the image based on its id at the given coordinates."""
        if self.touchscreen is None:
            return

        name = f"simulation_image_{TSImage.get_name_from_id(id)}"

        img = {
            "name": name,
            "type": "xy",
            "id": id,
            "centerX": cx,
            "centerY": cy,
            "rotation": 0,
            "scale": 1,
            "unit": unit,
        }
        self.touchscreen.setXYImage(
            img["name"],
            img["id"],
            img["centerX"],
            img["centerY"],
            img["rotation"],
            img["scale"],
            img["unit"],
        )
        self.update()

    def clear_all_images(self):
        """Clear all images from the display."""
        if self.touchscreen is None:
            return
        self.touchscreen.clear()
        self.update()

    def set_mode(self, mode: str):
        """Set the mode of the touchscreen device."""
        if not isinstance(self.touchscreen, TouchScreen2):
            return
        if mode == "normal":
            self.touchscreen.setNormalMode()
        if mode == "mouse":
            self.touchscreen.setMouseMode()
        if mode == "rat":
            self.touchscreen.setRatMode()

    def set_image_size(self, size: int | float, unit: str = "px"):
        """Set the size of the images on the touchscreen device."""
        if not isinstance(self.touchscreen, TouchScreen2):
            return
        self.touchscreen.setImageSize(size, unit)

    def ask_image_size(self):
        """Ask the user for the size of the images on the touchscreen device."""
        if not isinstance(self.touchscreen, TouchScreen2):
            return

        # ask unit (px or ratio)
        unit_item, ok = QInputDialog.getItem(
            self, "Image Size Unit", "Unit:", ["px", "ratio"], 0, False
        )
        if not ok:
            return
        unit = str(unit_item)

        # ask size (int or float)
        if unit == "px":
            size, ok_size = QInputDialog.getInt(
                self,
                "Image Size",
                f"Size ({unit}):",
                256,
                1,
                2000,
            )
        else:
            size, ok_size = QInputDialog.getDouble(
                self,
                "Image Size",
                f"Size ({unit}):",
                0.5,
                0.0,
                1.0,
                3,
            )

        if not ok_size:
            return

        self.set_image_size(size, unit)

    def user_touch(self, img: dict[str, Any]):
        if self.touchscreen is None:
            return

        desc = (
            f"symbol xy touched {img['name']} id {img['id']} "
            f"at display_ratio: {img['centerX']:.3f},{img['centerY']:.3f} "
            f"px: {int(img['centerX'])},{int(img['centerY'])},"
            f"{int(img['centerX'])},{int(img['centerY'])}"
        )
        data = (
            img["name"],
            img["id"],
            img["centerX"],
            img["centerY"],
            img["centerX"],
            img["centerY"],
            img["centerX"],
            img["centerY"],
        )
        self.touchscreen.fireEvent(
            DeviceEvent(
                "touchscreen",
                self.touchscreen,
                desc,
                data,
            )
        )

    def toggle_calibration(self):
        """Toggle the calibration mode of the touchscreen device."""
        self.show_calibration = not self.show_calibration
        self.update()
        if not isinstance(self.touchscreen, TouchScreen2):
            return
        self.touchscreen.toggleCalibration()

    def closeEvent(self, event: QCloseEvent):  # type: ignore[override]
        """Clean up when the widget is closed by the window manager (X button).

        Detach the device listener and attempt an orderly shutdown of the
        bound touchscreen/device threads, then quit the QApplication so the
        process exits.
        """
        # Detach listener if any
        if self.touchscreen is not None:
            self.touchscreen.removeDeviceListener(
                self.widget_touchscreen_listener
            )
            self.touchscreen.shutdown()
        super().closeEvent(event)


def test_mode(com_port: str, widget_angle: int = 0):
    """Test mode: open the widget to control the physical touchscreen device on
    the given COM port. The widget orientation can be set with the
    `widget_angle` parameter (-90, 0, 90, 180)."""
    import sys

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    app.setApplicationName("WTouchScreen Test Mode")

    widget_ts = WTouchScreen(angle=widget_angle)
    widget_ts.setName("TouchScreen Widget - Test Mode")

    ts = TouchScreen2(com_port)
    widget_ts.bindToTouchScreen(ts)

    widget_ts.show()

    screen = app.primaryScreen()

    if screen is not None:
        screen_size = screen.size()
        widget_ts.move(
            screen_size.width() // 3 - widget_ts.width() // 2,
            screen_size.height() // 3 - widget_ts.height() // 2,
        )
    widget_ts.display_image(29, cx=0.25, cy=0.5)
    widget_ts.display_image(30, cx=0.75, cy=0.5)
    input()
    ts.crash()
    sys.exit(app.exec())

    return widget_ts
