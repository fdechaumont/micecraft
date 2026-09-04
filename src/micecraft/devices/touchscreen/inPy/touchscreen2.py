import math
import random
import traceback
from time import sleep
from typing import Any
from pathlib import Path

import pygame
import serial

from ts_img_manager import TSImage


class Area:
    """A rectangular area defined relative to the real screen. Can convert
    coordinates between the area and the screen.

        The area is defined by :
        - its center (cx, cy) in normalized coordinates (0.0 - 1.0)
        - its size (width, height) in normalized coordinates (0.0 - 1.0)
        - its rotation in degrees (CCW) around the area center
        - if its axes need to be inverted or not

        Note: to create the real screen as an area:
        - center: (0.5, 0.5)
        - size: (1.0, 1.0)
        - rotation: 0.0
        - axis inversion: (False, False)
    """

    SCREEN: tuple[int, int] = (1920, 1080)
    """Real screen size in pixels (width, height)"""

    def __init__(
        self,
        cx: float = 0.5,
        cy: float = 0.5,
        width: float = 1.0,
        height: float = 1.0,
        rotation: float = 0.0,
        invert_axis: tuple[bool, bool] = (False, False),
    ):
        self.center: tuple[float, float] = (cx, cy)
        """(x, y) in normalized coordinates (0.0 - 1.0)"""
        self.size: tuple[float, float] = (width, height)
        """(width, height) in normalized coordinates (0.0 - 1.0)"""
        self.rotation: float = rotation % 360
        """angle in degrees (CCW)"""
        self.invert_axis: tuple[bool, bool] = invert_axis
        """(invert_x, invert_y)"""

    def set_center(self, x: float, y: float) -> None:
        self.center = (x, y)

    def set_size(self, width: float, height: float) -> None:
        self.size = (width, height)
        self._size_px = self.get_size_px()

    def set_rotation(self, rotation: float) -> None:
        self.rotation = rotation % 360
        self._size_px = self.get_size_px()

    def set_axis_inversion(self, invert_x: bool, invert_y: bool) -> None:
        self.invert_axis = (invert_x, invert_y)

    def screen_to_area(self, point: tuple[float, float]):
        """Convert normalized screen coordinates (0..1) to area normalized
        coordinates (0..1). Perform rotation in pixel space so the screen
        aspect ratio is handled correctly.
        """
        x, y = point

        # Axes inversion (undo)
        if self.invert_axis[0]:
            x = 1.0 - x
        if self.invert_axis[1]:
            y = 1.0 - y

        # Conversion (screen ratio -> pixels)
        px_x, px_y = self.screen_ratio_to_px((x, y))

        # Translation (origin = area center)
        px_cx, px_cy = self.get_center_px()
        px_x = px_x - px_cx
        px_y = px_y - px_cy

        # Rotation (inverted)
        theta = math.radians(-self.rotation)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        rot_px_x = int(round(px_x * cos_t - px_y * sin_t))
        rot_px_y = int(round(px_x * sin_t + px_y * cos_t))

        # Conversion (pixels -> area ratio)
        x, y = self.px_to_area_ratio((rot_px_x, rot_px_y))

        # Translation (origin = top-left corner of area)
        x = x + 0.5
        y = y + 0.5

        return x, y

    def area_to_screen(self, point: tuple[float, float]):
        """Convert normalized area coords (0..1) to normalized screen coords
        (0..1) by doing the transform in pixel space (handles aspect ratio).
        """
        x, y = point

        # Translation (origin = area center)
        x = x - 0.5
        y = y - 0.5

        # Conversion (area ratio -> pixels)
        px_x, px_y = self.area_ratio_to_px((x, y))

        # Rotation
        theta = math.radians(self.rotation)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        rot_px_x = int(round(px_x * cos_t - px_y * sin_t))
        rot_px_y = int(round(px_x * sin_t + px_y * cos_t))

        # Translation (origin = top-left corner of screen)
        px_cx, px_cy = self.get_center_px()
        px_x = rot_px_x + px_cx
        px_y = rot_px_y + px_cy

        # Conversion (pixels -> screen ratio)
        x, y = self.px_to_screen_ratio((px_x, px_y))

        # Axes inversion
        if self.invert_axis[0]:
            x = 1.0 - x
        if self.invert_axis[1]:
            y = 1.0 - y

        return x, y

    def get_size_px(self) -> tuple[int, int]:
        """Calculate and return the size of the area in pixels."""
        return (
            int(round(self.size[0] * self.SCREEN[0])),
            int(round(self.size[1] * self.SCREEN[1])),
        )

    def get_center_px(self) -> tuple[int, int]:
        """Calculate and return the center of the area in pixels."""
        return (
            int(round(self.center[0] * self.SCREEN[0])),
            int(round(self.center[1] * self.SCREEN[1])),
        )

    def area_ratio_to_px(self, point: tuple[float, float]) -> tuple[int, int]:
        """Convert normalized area coordinates (0..1) to pixel coordinates
        relative to the area size.
        """
        x, y = point
        px_w, px_h = self.get_size_px()
        px_x = int(round(x * px_w))
        px_y = int(round(y * px_h))
        return px_x, px_y

    def px_to_area_ratio(self, point: tuple[int, int]) -> tuple[float, float]:
        """Convert pixel coordinates relative to the area size to normalized
        area coordinates (0..1).
        """
        x, y = point
        px_w, px_h = self.get_size_px()
        r_x = x / px_w
        r_y = y / px_h
        return r_x, r_y

    @classmethod
    def screen_ratio_to_px(cls, point: tuple[float, float]) -> tuple[int, int]:
        """Convert normalized screen coordinates (0..1) to pixel coordinates
        relative to the screen size.
        """
        x, y = point
        sw, sh = cls.SCREEN
        px_x = int(round(x * sw))
        px_y = int(round(y * sh))
        return px_x, px_y

    @classmethod
    def px_to_screen_ratio(cls, point: tuple[int, int]) -> tuple[float, float]:
        """Convert pixel coordinates relative to the screen size to normalized
        screen coordinates (0..1).
        """
        x, y = point
        sw, sh = cls.SCREEN
        r_x = x / sw
        r_y = y / sh
        return r_x, r_y


class ScreenImage:
    """An image to display in display ratio (1.0 - 0.0)."""

    OFFSET: tuple[float, float] = (0, 0)
    """images offset (dx, dy) in display ratio (1.0 - 0.0)"""
    SIZE: int = 256
    """images size in pixels."""
    ALPHA: int = 255
    """images transparency (0-255)."""

    def __init__(
        self,
        surface: pygame.Surface,
        center: tuple[float, float],
        name: str,
        idx: int | None,
        rotation: float = 0.0,
    ):
        self.surface: pygame.Surface = surface
        """pygame.Surface of the image to display"""
        self.center: tuple[float, float] = center
        """center of image (cx, cy) in display ratio (1.0 - 0.0)"""
        self.name: str = name
        """name of the image"""
        self.idx: int | None = idx
        """index of the image, None if not from list"""
        self.rotation: float = rotation % 360
        """rotation of the image in degrees (CCW)"""

    def __str__(self) -> str:
        return self.name

    def get_center(self) -> tuple[float, float]:
        """Return the center of the image in display ratio (1.0 - 0.0)."""
        cx, cy = self.center
        dx, dy = self.OFFSET
        return (cx + dx, cy + dy)


class ScreenTouch:
    """A touch point to display in display ratio (1.0 - 0.0)."""

    OFFSET: tuple[float, float] = (0, 0)
    """touches offset (dx, dy) in display ratio (1.0 - 0.0)"""
    CROSS: tuple[int, int] = (40, 5)
    """(size, thickness) of the cross in pixels"""

    def __init__(
        self,
        surface: pygame.Surface,
        touch_id: Any,
        center: tuple[float, float],
    ):
        self.touch_id: Any = touch_id
        """unique identifier of the touch"""
        self.center: tuple[float, float] = center
        """center of touch (cx, cy) in display ratio (1.0 - 0.0)"""
        self.surface = surface
        """pygame.Surface of the touch to display"""

    def get_center(self) -> tuple[float, float]:
        """Return the center of the touch in display ratio (1.0 - 0.0)."""
        cx, cy = self.center
        dx, dy = self.OFFSET
        return (cx + dx, cy + dy)


class ScreenDisplayManager:
    """Pygame display manager.

    All image positions are expressed as normalized coordinates (0.0 - 1.0)
    *within the active area*.  The active area itself is expressed as
    normalized coordinates relative to the full display.

    Pixel unit only concern the screen display (full size). All other
    coordinates are expressed in normalized coordinates (0.0 - 1.0) relative to
    the corresponding area (display, screen, detector).
    """

    def __init__(self):
        """Create a pygame window."""
        pygame.init()

        # Create the screen display first.
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        """Whole Screen."""

        Area.SCREEN = self.screen.get_size()

        pygame.display.set_caption("LMT TouchScreen")
        pygame.mouse.set_visible(False)

        self.display_area = Area()
        """active area of the screen (portion of the full screen)"""

        self.detector_area = Area()
        """area corresponding to touch detector"""

        self.images: list[ScreenImage] = []
        """all displayed images (first in first drawn)"""

        self.touches: dict[Any, ScreenTouch] = {}
        """current touch positions, keyed by touch ID"""

        self.show_calibration: bool = False
        """Whether to show calibration lines or not."""

        self.clock = pygame.time.Clock()
        """pygame clock for frame rate limiting"""

        self.set_normal_mode()

        self.background: pygame.Surface | None = None
        """background surface of the display"""

    # Utilities
    # ----------------
    def display_ratio_to_px(self, point: tuple[float, float]):
        """Convert a value to pixels from display ratio."""
        px_point = self.display_area.area_ratio_to_px(point)
        return px_point

    def px_to_display_ratio(self, point: tuple[int, int]):
        """Convert a value to display ratio from pixels."""
        ratio_point = self.display_area.px_to_area_ratio(point)
        return ratio_point

    def screen_ratio_to_px(self, point: tuple[float, float]):
        """Convert a value to pixels from screen ratio."""
        px_point = self.display_area.screen_ratio_to_px(point)
        return px_point

    def px_to_screen_ratio(self, point: tuple[int, int]):
        """Convert a value to screen ratio from pixels."""
        ratio_point = self.display_area.px_to_screen_ratio(point)
        return ratio_point

    def detector_ratio_to_px(self, point: tuple[float, float]):
        """Convert a value to pixels from detector ratio."""
        px_point = self.detector_area.area_ratio_to_px(point)
        return px_point

    def px_to_detector_ratio(self, point: tuple[int, int]):
        """Convert a value to detector ratio from pixels."""
        ratio_point = self.detector_area.px_to_area_ratio(point)
        return ratio_point

    def clear(self) -> None:
        """Clear all images and touches from the display."""
        self.screen.fill((0, 0, 0))
        self.remove_all_images()
        self.remove_all_touches()
        self.background = None

    # Image
    # ----------------
    def create_display_surface(
        self,
        color: tuple[int, int, int] = (0, 0, 0),
        alpha: int = 255,
    ) -> pygame.Surface:
        """Create a square pygame.Surface of the specified size and color."""
        aw, ah = self.display_area.get_size_px()
        sw, sh = Area.SCREEN
        aw = max(0, min(aw, sw))
        ah = max(0, min(ah, sh))
        area_size = (aw, ah)
        surface = pygame.Surface(area_size, flags=pygame.SRCALPHA)
        surface.fill((*color, alpha))
        return surface

    def add_image(
        self,
        image: ScreenImage,
    ) -> None:
        """Add or update a surface centered at the given active-area position.

        Args:
            surface: A pygame.Surface to display.
            x:  Horizontal center in pixels within the active area.
            y:  Vertical center in pixels within the active area.
            name:    Unique slot identifier.  Overwrites any existing entry.
        """
        self.images.append(image)

    def remove_image(self, name: str) -> None:
        self.images = [img for img in self.images if img.name != name]

    def remove_all_images(self) -> None:
        self.images.clear()

    def remove_all_touches(self) -> None:
        self.touches.clear()

    def remove_background(self) -> None:
        self.background = None

    # Touches
    # ----------------
    def add_touch(self, touch_id: Any, point: tuple[float, float]):
        """Register an active touch point (display ratio)."""
        ts, tt = ScreenTouch.CROSS
        s = pygame.Surface((ts, ts), pygame.SRCALPHA)
        pygame.draw.line(s, (255, 0, 0), (0, 0), (ts, ts), tt)
        pygame.draw.line(s, (255, 0, 0), (0, ts), (ts, 0), tt)
        touch = ScreenTouch(s, touch_id, point)
        self.touches[touch_id] = touch
        return touch

    def remove_touch(self, touch_id: Any) -> None:
        if touch_id in self.touches:
            self.touches.pop(touch_id)

    def hit_test(self, touch: ScreenTouch) -> list[ScreenImage]:
        """Return the list of images whose bounding rect contains specified
        Screentouch."""
        images_touched = []
        for img in self.images:
            cx, cy = img.get_center()
            tx, ty = touch.get_center()

            # Translation (origin = image center)
            tx = tx - cx
            ty = ty - cy

            # Conversion (area ratio -> pixels)
            tx_px, ty_px = self.display_ratio_to_px((tx, ty))

            # Rotation
            theta = math.radians(img.rotation)
            cos_t = math.cos(theta)
            sin_t = math.sin(theta)
            tx_rot_px = int(round(tx_px * cos_t - ty_px * sin_t))
            ty_rot_px = int(round(tx_px * sin_t + ty_px * cos_t))

            sw_px, sh_px = img.surface.get_size()
            x_min_px = -round(sw_px / 2) - 1
            x_max_px = round(sw_px / 2) + 1
            y_min_px = -round(sh_px / 2) - 1
            y_max_px = round(sh_px / 2) + 1

            if (x_min_px <= tx_rot_px <= x_max_px) and (
                y_min_px <= ty_rot_px <= y_max_px
            ):
                images_touched.append(img)

        return images_touched

    # Calibration
    # ----------------
    def set_show_calibration(self, enabled: bool) -> None:
        self.show_calibration = enabled

    def toggle_calibration(self) -> None:
        self.show_calibration = not self.show_calibration

    def get_axes_surface(
        self,
        name: str,
        size: int,
        color: tuple[int, int, int],
        font: pygame.font.Font,
        line_width: int = 3,
    ) -> pygame.Surface:
        """Return a surface with a horizontal and vertical axis drawn."""
        axes = pygame.Surface((size, size), flags=pygame.SRCALPHA)
        # X axis (right)
        pygame.draw.line(
            axes,
            color,
            (0, size // 2),
            (size, size // 2),
            line_width,
        )
        pygame.draw.polygon(
            axes,
            color,
            [
                (size, size // 2),
                (size - 3 * line_width, size // 2 - 2 * line_width),
                (size - 3 * line_width, size // 2 + 2 * line_width),
            ],
        )
        # Y axis (down)
        pygame.draw.line(
            axes,
            color,
            (size // 2, 0),
            (size // 2, size),
            line_width,
        )
        pygame.draw.polygon(
            axes,
            color,
            [
                (size // 2, size),
                (size // 2 - 2 * line_width, size - 3 * line_width),
                (size // 2 + 2 * line_width, size - 3 * line_width),
            ],
        )
        # graph name
        txt = font.render(name, True, color)
        axes.blit(
            txt,
            (
                size // 2 - txt.get_width() - line_width,
                size // 2 - txt.get_height() - line_width,
            ),
        )
        # X axis
        txt = font.render("X axis", True, color)
        axes.blit(
            txt,
            (
                size - txt.get_width(),
                size // 2 + 3 * line_width,
            ),
        )
        # Y axis
        txt = font.render("Y axis", True, color)
        axes.blit(
            txt,
            (
                size // 2 + 3 * line_width,
                size - txt.get_height(),
            ),
        )
        return axes

    def get_calibration(self):
        """Return a pygame.Surface with calibration lines and extra
        diagnostic drawings.

        The surface is divided by the central cross into four quarters.
        Top-left: active-area axis arrows (green)
        Top-right: absolute screen axis arrows (blue)
        Bottom-left: area dimensions and transform (px / ratio)
        Bottom-right: two equally sized squares of 100 pixels.
        """
        cali = self.create_display_surface(alpha=0)

        aw, ah = self.display_area.get_size_px()
        sw, sh = self.display_area.SCREEN

        # Font
        # ----------------
        try:
            font = pygame.font.SysFont(None, 16)
        except Exception:
            pygame.font.init()
            font = pygame.font.SysFont(None, 16)

        # Lines
        # ----------------
        # area lines (green)
        pygame.draw.rect(cali, (0, 255, 0), (0, 0, aw, ah), 3)
        pygame.draw.line(cali, (0, 255, 0), (aw // 2, 0), (aw // 2, ah), 3)
        pygame.draw.line(cali, (0, 255, 0), (0, ah // 2), (aw, ah // 2), 3)

        # screen center (blue)
        screen_center = (0.5, 0.5)
        screen_center = self.display_area.screen_to_area(screen_center)
        screen_center = self.display_area.area_ratio_to_px(screen_center)
        pygame.draw.circle(cali, (0, 0, 0), screen_center, 13)
        pygame.draw.circle(cali, (0, 200, 200), screen_center, 6)

        # Top-left: active-area axes
        # ----------------
        axes = self.get_axes_surface(
            "DISPLAY", min(aw, ah) // 3, (0, 255, 0), font
        )
        tl_x = aw // 4
        tl_y = ah // 4
        cali.blit(
            axes,
            (tl_x - axes.get_width() // 2, tl_y - axes.get_height() // 2),
        )

        # Top-right: screen axes
        # ----------------
        # Compute an anchor in screen space (near top-right) and map it
        # into area coordinates so the arrows indicate the absolute
        # screen +X/+Y directions (not the area axes).
        axes = self.get_axes_surface(
            "SCREEN", min(aw, ah) // 3, (0, 200, 200), font
        )
        tr_x = 3 * aw // 4
        tr_y = ah // 4
        axes = pygame.transform.rotate(axes, -self.display_area.rotation)
        cali.blit(
            axes,
            (tr_x - axes.get_width() // 2, tr_y - axes.get_height() // 2),
        )

        # Bottom-left: area dimensions and transform
        # ----------------
        bl_x = aw // 4
        bl_y = 3 * ah // 4
        aw_ratio = aw / sw
        ah_ratio = ah / sh
        angle = self.display_area.rotation
        cx, cy = self.display_area.get_center_px()

        lines = [
            f"display: {aw} x {ah} px",
            f"center: ({cx}, {cy}) px",
            f"angle: {angle:.0f} deg",
            f"display: {aw_ratio:.2f} x {ah_ratio:.2f} screen ratio",
            f"center: ({cx / sw:.2f}, {cy / sh:.2f}) screen ratio",
        ]

        # Pre-render lines and compute block size so we can center it in
        # the bottom-left quadrant (center at (bl_x, bl_y)).
        rendered = [font.render(L, True, (255, 255, 0)) for L in lines]
        max_w = max(s.get_width() for s in rendered)
        total_h = (
            sum(s.get_height() for s in rendered) + (len(rendered) - 1) * 4
        )

        start_x = bl_x - max_w // 2
        start_y = bl_y - total_h // 2

        oy = 0
        for surf_txt in rendered:
            # center each line within the block
            x = start_x + (max_w - surf_txt.get_width()) // 2
            y = start_y + oy
            cali.blit(surf_txt, (x, y))
            oy += surf_txt.get_height() + 4

        # Bottom-right: two equally sized squares of 100 pixels
        # ----------------
        size_px = 100
        gap = 12
        br_area_x = 3 * aw // 4
        br_area_y = 3 * ah // 4

        total_width = 2 * size_px + gap
        start_x = int(br_area_x - total_width / 2)
        start_y = int(br_area_y - size_px / 2)

        for i in range(2):
            rx = max(0, min(aw - size_px, start_x + i * (size_px + gap)))
            ry = max(0, min(ah - size_px, start_y))
            pygame.draw.rect(
                cali, (255, 255, 255), (rx, ry, size_px, size_px), 2
            )
            labels = []
            if i == 0:
                labels.append(f"{size_px}")
                labels.append("x")
                labels.append(f"{size_px}")
                labels.append("pixels")
            else:
                size_ratio = self.px_to_display_ratio((size_px, size_px))
                labels.append(f"{size_ratio[0]:.2f}")
                labels.append("x")
                labels.append(f"{size_ratio[1]:.2f}")
                labels.append("display ratio")
            txt = [font.render(l, True, (255, 255, 255)) for l in labels]
            total_h = sum(s.get_height() for s in txt) + (len(txt) - 1) * 4
            oy = (size_px - total_h) // 2
            for s in txt:
                x = rx + (size_px - s.get_width()) // 2
                cali.blit(s, (x, ry + oy))
                oy += s.get_height() + 4

        # Corners: indicate area coordinates
        # ----------------
        corners = [(0, 0), (1, 0), (0, 1), (1, 1), (0.5, 0.5)]
        for c in corners:
            px_c = self.display_area.area_ratio_to_px(c)
            label = f"({c[0]}, {c[1]})"
            txt = font.render(label, True, (0, 255, 0))
            if c[0] == 0:
                px_cx = px_c[0] + txt.get_width() // 2 + 12
            else:
                px_cx = px_c[0] - txt.get_width() // 2 - 12
            if c[1] == 0:
                px_cy = px_c[1] + txt.get_height() // 2 + 12
            else:
                px_cy = px_c[1] - txt.get_height() // 2 - 12
            cali.blit(
                txt,
                (
                    px_cx - txt.get_width() // 2,
                    px_cy - txt.get_height() // 2,
                ),
            )

        return cali

    # Mode
    # ----------------
    def set_mode(
        self,
        display_size: tuple[float, float] = (1, 1),
        display_center: tuple[float, float] = (0.5, 0.5),
        display_rotation: float = 0,
        display_invert_axis: tuple[bool, bool] = (False, False),
        detector_size: tuple[float, float] = (1.0, 1.0),
        detector_center: tuple[float, float] = (0.5, 0.5),
        detector_rotation: float = 0,
        detector_invert_axis: tuple[bool, bool] = (False, False),
    ) -> None:
        """Set the display mode by specifying the active area size, center and
        rotation.

        The working detector size (relative to screen size) is:
        - 1.40 x 2.00 for mouse mode
        - 0.95 x 1.40 for rat mode

        Rotations are clockwise in degrees. The touch detector cable goes out
        at the bottom-right corner when in normal orientation (0 degrees
        rotation)."""
        self.display_area.size = display_size
        self.display_area.center = display_center
        self.display_area.rotation = display_rotation % 360
        self.display_area.invert_axis = display_invert_axis

        self.detector_area.size = detector_size
        self.detector_area.center = detector_center
        self.detector_area.rotation = detector_rotation % 360
        self.detector_area.invert_axis = detector_invert_axis

    def set_normal_mode(self) -> None:
        """Set the display to normal mode."""
        self.set_mode()

    def set_mouse_mode(self) -> None:
        """Set the display to mouse mode."""

        # Screen display
        # ----------------
        sd_size = (0.80, 0.65)  # relative to screen size
        sd_center = (0.5, 1 - sd_size[1] / 2)

        # Touch detector
        # ----------------
        td_size = (1.4, 2.0)  # relative to screen size
        td_center = (0.5, 0.65)
        td_rotation = -90  # cable goes out at top-right corner

        # Mode setting
        # ----------------
        self.set_mode(
            display_size=sd_size,
            display_center=sd_center,
            detector_size=td_size,
            detector_center=td_center,
            detector_rotation=td_rotation,
        )

    def set_rat_mode(self) -> None:
        """Set the display to rat mode."""
        # Screen display
        # ----------------
        sd_size = (0.95, 0.82)  # relative to screen size
        sd_center = (0.5, 1 - sd_size[1] / 2)

        # Touch detector
        # ----------------
        td_size = (0.95, 1.40)  # relative to screen size
        td_center = (0.5, 1 - 1.40 / 2 + 0.05)  # bottom aligned
        td_rotation = 180  # cable goes out at top-left corner

        # Mode setting
        # ----------------
        self.set_mode(
            display_size=sd_size,
            display_center=sd_center,
            detector_size=td_size,
            detector_center=td_center,
            detector_rotation=td_rotation,
        )

    # Rendering
    # ----------------

    def render(self, fps: int = 30) -> None:
        """Clear the display, blit all images, optionally draw calibration,
        flip."""

        self.screen.fill((0, 0, 0))  # clear the display to black

        # create area copy to draw on
        area = self.create_display_surface()

        # blit background if any
        if self.background is not None:
            area.blit(self.background, (0, 0))

        # blit all images
        for img in self.images:
            s = img.surface
            s = pygame.transform.rotate(s, img.rotation)
            cx, cy = self.display_ratio_to_px(img.get_center())
            x = cx - s.get_width() // 2
            y = cy - s.get_height() // 2
            area.blit(s, (x, y))

        # draw calibration and touches if enabled
        if self.show_calibration:
            cali = self.get_calibration()
            area.blit(cali, (0, 0))

            # blit all touches
            for touch in self.touches.values():
                s = touch.surface
                cx, cy = self.display_ratio_to_px(touch.get_center())
                x = cx - s.get_width() // 2
                y = cy - s.get_height() // 2
                area.blit(s, (x, y))

        # rotate window
        angle = self.display_area.rotation
        area = pygame.transform.rotate(area, angle)

        # translate window
        cx, cy = self.display_area.get_center_px()
        w, h = area.get_size()
        tx = cx - w // 2
        ty = cy - h // 2

        # blit window
        self.screen.blit(area, (tx, ty))

        # update display
        pygame.display.update()

        # limit the frame rate
        self.clock.tick(fps)

    def quit(self) -> None:
        pygame.quit()


class TouchScreen:
    """Serial communication layer and image/surface lifecycle manager.

    Reads commands from a serial port and dispatches them to a ScreenManager.
    Also creates pygame.Surfaces (from files or procedurally) and registers
    them with the ScreenManager.
    """

    def __init__(
        self,
        test_mode: bool = False,
    ):

        print("Starting TouchScreen")

        if not test_mode:
            print("Starting serial...")
            self.ser = serial.Serial(
                "/dev/ttyS0",
                baudrate=115200,
                write_timeout=2,
                timeout=0,
            )  # 115200
            # parity = serial.PARITY_ODD
            # stopbits = serial.STOPBITS_TWO
            # bytesize = serial.SEVENBITS
            print(self.ser.name)
            self.send("Starting touchscreen...")
        else:
            self.ser = None
            self.send("Test mode: no serial")

        self.last_error: str = ""
        self.input_buffer: str = ""
        self.manager = ScreenDisplayManager()
        self.running: bool = True
        self._loaded_images: dict[int, pygame.Surface] = {}
        """Dictionary of loaded images: id -> surface"""

        self.send("Touchscreen started")

    # Parameters
    # ----------------
    def getScreenSize(self) -> tuple[int, int]:
        """Return the size of the full screen in pixels."""
        return self.manager.screen.get_size()

    def getAreaSize(self) -> tuple[int, int]:
        """Return the size of the active area in pixels."""
        return self.manager.display_area.get_size_px()

    def getImageSize(self) -> int:
        """Return the size of images in pixels."""
        return ScreenImage.SIZE

    def setImageSize(
        self,
        size: int,
    ) -> None:
        """Set the size of images in pixels."""
        ScreenImage.SIZE = size
        self.load_all_images()

    def setImageOffset(
        self,
        dx: float,
        dy: float,
    ) -> None:
        """Set a global offset for all images in display ratio."""
        ScreenImage.OFFSET = (dx, dy)

    def setTouchOffset(
        self,
        dx: float,
        dy: float,
    ) -> None:
        """Set a global offset for all touches in pixels."""
        ScreenTouch.OFFSET = (dx, dy)

    # Calibration
    # ----------------
    def setShowCalibration(self, enabled: bool) -> None:
        self.manager.show_calibration = bool(enabled)

    def toggleCalibration(self) -> None:
        self.manager.show_calibration = not self.manager.show_calibration

    # Finger touches
    # ----------------

    def check_if_touch_on_image(
        self,
        touch: ScreenTouch,
        px_screen_pos: tuple[int, int],
    ) -> None:
        images_touched = self.manager.hit_test(touch)
        t_center = touch.get_center()
        if images_touched:
            for image in images_touched:
                i_center = image.get_center()
                i_center_px = self.manager.display_ratio_to_px(i_center)
                self.send(
                    f"symbol xy touched {image.name} id {image.idx} "
                    f"at display_ratio: {t_center[0]:.3f},{t_center[1]:.3f} "
                    f"px: {i_center_px[0]},{i_center_px[1]},"
                    f"{px_screen_pos[0]},{px_screen_pos[1]}"
                )
        else:
            self.send(
                f"missed display_ratio: {t_center[0]:.3f},{t_center[1]:.3f} "
                f"px: {px_screen_pos[0]},{px_screen_pos[1]}"
            )

    # Surface creation
    # ----------------

    def load_image(self, filepath: Path) -> pygame.Surface:
        """Load an image file and create a pygame.Surface."""
        surf = pygame.image.load(filepath).convert_alpha()
        w, h = surf.get_size()
        scale = ScreenImage.SIZE / max(w, h)
        surf = pygame.transform.scale(surf, (int(w * scale), int(h * scale)))
        surf.fill(
            (255, 255, 255, ScreenImage.ALPHA),
            special_flags=pygame.BLEND_RGBA_MULT,
        )
        return surf

    def load_all_images(self) -> None:
        """Load all images in current working directory and register them."""
        list_paths = TSImage.get_images_path()

        for idx, path in list_paths.items():
            surf = self.load_image(path)
            self._loaded_images[idx] = surf

    def getImage(self, index: int) -> pygame.Surface:
        """Return the pygame.Surface for a given image index, or None if not found."""
        image = None
        try:
            image = self._loaded_images[index]
        except:
            self.send_error_feedback(f"getImage: Image key error:{index}")
            image = self._loaded_images[0]  # error image
        return image

    def getStripe(
        self,
        thickness1: int = 10,
        thickness2: int = 10,
        angle: float = 0.0,
        color1: tuple = (255, 255, 255),
        color2: tuple = (0, 0, 0),
    ) -> pygame.Surface:
        """Create a striped surface with specified colors and thicknesses."""
        t1 = max(0, int(thickness1))
        t2 = max(0, int(thickness2))
        stripe_height = t1 + t2

        if stripe_height <= 0:
            return pygame.Surface(
                (ScreenImage.SIZE, ScreenImage.SIZE),
                flags=pygame.SRCALPHA,
            )

        diag = math.ceil(math.hypot(ScreenImage.SIZE, ScreenImage.SIZE))

        surf = pygame.Surface(
            (diag, diag),
            flags=pygame.SRCALPHA,
        )

        for y in range(0, diag, stripe_height):
            if t1 > 0:
                pygame.draw.rect(surf, color1, (0, y, diag, t1))
            if t2 > 0:
                pygame.draw.rect(surf, color2, (0, y + t1, diag, t2))

        surf = pygame.transform.rotate(surf, angle % 180)

        x = surf.get_width() // 2 - ScreenImage.SIZE // 2
        y = surf.get_height() // 2 - ScreenImage.SIZE // 2
        final = pygame.Surface(
            (ScreenImage.SIZE, ScreenImage.SIZE),
            flags=pygame.SRCALPHA,
        )
        final.blit(surf, (-x, -y))
        return final

    def setXYImage(
        self,
        name: str,
        index: int,
        cx: float,
        cy: float,
        r: float = 0.0,
        s: float = 1.0,
    ) -> None:
        """Set an image by its center coordinates (cx, cy) in display ratio
        (0.0 - 1.0).

        Parameters:
        -----------
        name: str
            Name of the image.
        index: int
            Index of the image in the loaded images.
        cx: float
            X coordinate of the image center (display ratio).
        cy: float
            Y coordinate of the image center (display ratio).
        r: float
            Rotation angle in degrees.
        s: float
            Scale factor.
        """

        surf = self.getImage(index)
        if surf is None:
            self.send_error_feedback(
                f"setXYImage: index {index:03d} not found"
            )
            return
        surf = pygame.transform.rotozoom(surf, 0.0, s)
        image = ScreenImage(surf, (cx, cy), name, index, r)
        self.manager.add_image(image)

    def setXYStripes(
        self,
        name: str,
        cx: float,
        cy: float,
        r: float = 0.0,
        s: float = 1.0,
        stripe_angle: float = 0.0,
        thickness1: int = 10,
        thickness2: int = 10,
        color1: tuple = (255, 255, 255),
        color2: tuple = (0, 0, 0),
    ) -> pygame.Surface:
        """Set an image by its center coordinates (cx, cy) in display ratio
        (0.0 - 1.0).

        Parameters:
        -----------
        name: str
            Name of the image.
        cx: float
            X coordinate of the image center (display ratio).
        cy: float
            Y coordinate of the image center (display ratio).
        r: float
            Rotation angle in degrees.
        s: float
            Scale factor.
        stripe_angle: float
            Angle of the stripes in degrees.
        thickness1: int
            Thickness of the first stripe color in pixels.
        thickness2: int
            Thickness of the second stripe color in pixels.
        color1: tuple
            RGB color of the first stripe.
        color2: tuple
            RGB color of the second stripe.
        """
        surf = self.getStripe(
            thickness1,
            thickness2,
            stripe_angle,
            color1,
            color2,
        )
        surf = pygame.transform.rotozoom(surf, 0.0, s)
        image = ScreenImage(surf, (cx, cy), name, None, r)
        self.manager.add_image(image)
        return surf

    def removeXYImage(self, name: str) -> None:
        """Remove an image by its name."""
        self.manager.remove_image(name)

    def removeXYStripes(self, name: str) -> None:
        """Remove a striped image by its name."""
        self.manager.remove_image(name)

    def removeAllImages(self) -> None:
        """Remove all images from the screen."""
        self.manager.remove_all_images()

    # Background
    # ----------------
    def setBgColor(self, color: tuple[int, int, int]) -> None:
        """Set the background color of the screen."""
        self.manager.background = self.manager.create_display_surface(color)

    def setBgStripes(
        self,
        thickness1: int = 10,
        thickness2: int = 10,
        angle: float = 0.0,
        color1: tuple = (255, 255, 255),
        color2: tuple = (0, 0, 0),
    ) -> None:
        """Set the background to a striped pattern.

        Parameters:
        -----------
        thickness1: int
            Thickness of the first stripe color in pixels.
        thickness2: int
            Thickness of the second stripe color in pixels.
        angle: float
            Angle of the stripes in degrees.
        color1: tuple
            RGB color of the first stripe.
        color2: tuple
            RGB color of the second stripe.
        """

        aw, ah = self.manager.display_area.get_size_px()
        diag = math.ceil(math.hypot(aw, ah))

        big_bg = pygame.Surface((diag, diag), flags=pygame.SRCALPHA)

        stripe_height = thickness1 + thickness2
        t1 = thickness1
        t2 = thickness2

        for y in range(0, diag, stripe_height):
            if t1 > 0:
                pygame.draw.rect(big_bg, color1, (0, y, diag, t1))
            if t2 > 0:
                pygame.draw.rect(big_bg, color2, (0, y + t1, diag, t2))

        big_bg = pygame.transform.rotate(big_bg, angle % 180)

        x = (aw - big_bg.get_width()) // 2
        y = (ah - big_bg.get_height()) // 2
        self.manager.background = self.manager.create_display_surface()
        self.manager.background.blit(big_bg, (x, y))

    # Serial
    # ----------------

    def send(self, message: str) -> None:
        """Write a newline-terminated UTF-8 string to serial."""
        if self.ser is None:
            print(f"[no serial] {message}")
            return
        self.ser.write((message + "\n").encode("utf-8"))

    def send_error_feedback(self, error):
        # check error to avoid repeating the same one all the time
        if self.ser is None:
            print(f"[no serial] Touchscreen - error - traceback: {error}")
            return
        if self.last_error == error:
            return
        self.send(f"Touchscreen - error - traceback: {error}")
        self.last_error = error

    def read_command(self) -> str | None:
        """Non-blocking: read one complete line from serial, or return None."""
        if self.ser is None:
            return None

        data_in = self.ser.readline()
        try:
            data_in = data_in.decode()
        except Exception:
            self.send_error_feedback("Can't utf-8-decode command")
            return None

        self.input_buffer += data_in

        if "\n" not in self.input_buffer:
            return None

        line, _, self.input_buffer = self.input_buffer.partition("\n")

        return line.strip()

    def execute_command(self, command: str | None):
        """Parse a single serial command and act on it."""
        if command is None:
            return False
        print(f"process command: {command}")

        c = command.split(" ")

        if not c:
            return False

        if "hello" in c[0]:
            # hello
            self.send("Touchscreen - driver v2.2")
            return True

        if "ping" in c[0]:
            # ping
            self.send("pong")
            return True

        if "clear" in c[0]:
            # clear
            self.manager.clear()
            return True

        if "calibration" in c[0]:
            # calibration <show|hide|toggle>
            if "show" in command:
                self.manager.set_show_calibration(True)
            elif "hide" in command:
                self.manager.set_show_calibration(False)
            else:
                self.manager.toggle_calibration()
            return True

        if "removeAllImages" in c[0]:
            # removeAllImages
            self.manager.remove_all_images()
            return True

        if "setXYImage" in c[0]:
            # setXYImage <name> <id> <cx> <cy> <r> <s> <unit>
            name = c[1]
            idx = int(c[2])
            unit = c[7]
            if len(c) > 5:
                r = float(c[5])
            else:
                r = 0.0
            if len(c) > 6:
                s = float(c[6])
            else:
                s = 1.0

            if "px" in unit:
                cx, cy = self.manager.px_to_display_ratio(
                    (int(c[3]), int(c[4]))
                )
            elif "ratio" in unit:
                cx, cy = float(c[3]), float(c[4])
            else:
                self.send_error_feedback(f"setXYImage: unknown unit {unit}")
                return True
            self.setXYImage(name, idx, cx, cy, r, s)
            return True

        if "removeXYImage" in c[0]:
            # removeXYImage <name>
            self.manager.remove_image(c[1])
            return True

        if "setXYStripes" in c[0]:
            # setXYStripes <name> <cx> <cy> <r> <s> <stripe_angle> <thickness1> <thickness2> <color1> <color2> <unit>
            name = c[1]
            r = float(c[4])
            s = float(c[5])
            stripe_angle = float(c[6])
            thickness1 = int(c[7])
            thickness2 = int(c[8])
            color1 = tuple(map(int, c[9].split(",")))
            color2 = tuple(map(int, c[10].split(",")))

            unit = c[11]
            if "px" in unit:
                cx, cy = self.manager.px_to_display_ratio(
                    (int(c[2]), int(c[3]))
                )
            elif "ratio" in unit:
                cx, cy = float(c[2]), float(c[3])
            else:
                self.send_error_feedback(f"setXYStripes: unknown unit {unit}")
                return True

            self.setXYStripes(
                name,
                cx,
                cy,
                r,
                s,
                stripe_angle,
                thickness1,
                thickness2,
                color1,
                color2,
            )
            return True

        if "removeXYStripes" in c[0]:
            # removeXYStripes <name>
            self.manager.remove_image(c[1])
            return True

        if "removeImage" in c[0]:
            # removeImage <name>
            self.manager.remove_image(c[1])
            return True

        if "moveImage" in c[0]:
            # moveImage <name> <cx> <cy> <unit>
            unit = c[4]
            image = None
            for img in self.manager.images:
                if img.name == c[1]:
                    image = img
                    break
            if image is None:
                self.send_error_feedback(f"moveImage: image {c[1]} not found")
                return True

            if "px" in unit:
                image.center = self.manager.px_to_display_ratio(
                    (int(c[2]), int(c[3]))
                )
            if "ratio" in unit:
                image.center = (float(c[2]), float(c[3]))
            return True

        if "transparency" in c[0]:
            # transparency <value>
            ScreenImage.ALPHA = int(c[1])
            return True

        if "imageSize" in c[0]:
            # imageSize <value> <unit>
            unit = c[2]
            if "px" in unit:
                self.setImageSize(int(c[1]))
            if "ratio" in unit:
                dim = max(self.manager.display_area.get_size_px())
                self.setImageSize(int(float(c[1]) * dim))
            return True

        if "setBgColor" in c[0]:
            # setBgColor <r> <g> <b>
            r = int(c[1])
            g = int(c[2])
            b = int(c[3])
            self.setBgColor((r, g, b))
            return True

        if "setBgStripes" in c[0]:
            # setBgStripes <thickness1> <thickness2> <angle> <r1> <g1> <b1> <r2> <g2> <b2>
            thickness1 = int(c[1])
            thickness2 = int(c[2])
            angle = float(c[3])
            color1 = (int(c[4]), int(c[5]), int(c[6]))
            color2 = (int(c[7]), int(c[8]), int(c[9]))
            self.setBgStripes(thickness1, thickness2, angle, color1, color2)
            return True

        if "removeBg" in c[0]:
            # removeBg
            self.manager.remove_background()
            return True

        if "setImageOffset" in c[0]:
            # setImageOffset <dx> <dy> <unit>
            unit = c[3]
            if "px" in unit:
                dx, dy = self.manager.px_to_display_ratio(
                    (int(c[1]), int(c[2]))
                )
                self.setImageOffset(dx, dy)
            if "ratio" in unit:
                dx, dy = (float(c[1]), float(c[2]))
                self.setImageOffset(dx, dy)
            return True

        if "setTouchOffset" in c[0]:
            # setTouchOffset <dx> <dy> <unit>
            unit = c[3]
            if "px" in unit:
                self.setTouchOffset(int(c[1]), int(c[2]))
            if "ratio" in unit:
                dx, dy = self.manager.display_ratio_to_px(
                    (float(c[1]), float(c[2]))
                )
                self.setTouchOffset(dx, dy)
            return True

        if "mouseMode" in c[0]:
            # mouseMode
            self.manager.set_mouse_mode()
            return True

        if "ratMode" in c[0]:
            # ratMode
            self.manager.set_rat_mode()
            return True

        if "normalMode" in c[0]:
            # normalMode
            self.manager.set_normal_mode()
            return True

        if "setMode" in c[0]:
            # setMode <display_width_ratio> <display_height_ratio>
            # <display_center_x_ratio> <display_center_y_ratio>
            # <display_rotation_angle> <display_invert_x> <display_invert_y>
            # <detector_width_ratio> <detector_height_ratio>
            # <detector_center_x_ratio> <detector_center_y_ratio>
            # <detector_rotation_angle> <detector_invert_x> <detector_invert_y>
            default = (
                1,
                1,
                0.5,
                0.5,
                0,
                False,
                False,
                1,
                1,
                0.5,
                0.5,
                0,
                False,
                False,
            )
            if len(c) < 15:
                c += [str(x) for x in default[len(c) :]]
            d_w = float(c[1])
            d_h = float(c[2])
            d_cx = float(c[3])
            d_cy = float(c[4])
            d_rot = float(c[5])
            d_inv_x = c[6].lower() == "true" or int(c[6]) == 1
            d_inv_y = c[7].lower() == "true" or int(c[7]) == 1
            det_w = float(c[8])
            det_h = float(c[9])
            det_cx = float(c[10])
            det_cy = float(c[11])
            det_rot = float(c[12])
            det_inv_x = c[13].lower() == "true" or int(c[13]) == 1
            det_inv_y = c[14].lower() == "true" or int(c[14]) == 1
            self.manager.set_mode(
                display_size=(d_w, d_h),
                display_center=(d_cx, d_cy),
                display_rotation=d_rot,
                display_invert_axis=(d_inv_x, d_inv_y),
                detector_size=(det_w, det_h),
                detector_center=(det_cx, det_cy),
                detector_rotation=det_rot,
                detector_invert_axis=(det_inv_x, det_inv_y),
            )
            return True

        if "crash" in c[0]:
            raise Exception("Crash asked by user")

        return False

    # Processing
    # ----------------

    def process_commands(self) -> None:
        """Handle pygame events for one frame."""
        for _ in range(10):
            cmd = self.read_command()
            if self.execute_command(cmd):
                self.manager.render()
            if cmd is None:
                break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # Key-oriented controls (Q to quit, C to toggle calibration)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    self.running = False
                    print("Q or ESC key hit: exit")
                elif event.key == pygame.K_c:
                    self.manager.toggle_calibration()
                    print("C key hit: toggle calibration")
                elif event.key == pygame.K_o:
                    self.manager.clear()
                    print("O key hit: clear display")
                elif event.key == pygame.K_a:
                    self.removeAllImages()
                    print("A key hit: remove all images")
                elif event.key == pygame.K_i:
                    self.removeXYImage("random_image")
                    self.setXYImage(
                        "random_image",
                        random.choice(list(self._loaded_images.keys())),
                        random.random(),
                        random.random(),
                        random.uniform(0, 360),
                        random.uniform(0.5, 1.5),
                    )
                    print("I key hit: add random image at random position")
                elif event.key == pygame.K_s:
                    self.removeXYStripes("random_stripes")
                    self.setXYStripes(
                        "random_stripes",
                        random.random(),
                        random.random(),
                        random.uniform(0, 360),
                        random.uniform(0.5, 1.5),
                        random.uniform(0, 180),
                        random.randint(1, 50),
                        random.randint(1, 50),
                        (
                            random.randint(0, 255),
                            random.randint(0, 255),
                            random.randint(0, 255),
                        ),
                        (
                            random.randint(0, 255),
                            random.randint(0, 255),
                            random.randint(0, 255),
                        ),
                    )
                    print("S key hit: add random stripes at random position")
                elif event.key == pygame.K_b:
                    self.setBgColor(
                        (
                            random.randint(0, 255),
                            random.randint(0, 255),
                            random.randint(0, 255),
                        )
                    )
                    print("B key hit: set random background color")
                elif event.key == pygame.K_v:
                    self.setBgStripes(
                        random.randint(1, 500),
                        random.randint(1, 500),
                        random.uniform(0, 360),
                        (
                            random.randint(0, 255),
                            random.randint(0, 255),
                            random.randint(0, 255),
                        ),
                        (
                            random.randint(0, 255),
                            random.randint(0, 255),
                            random.randint(0, 255),
                        ),
                    )
                    print("V key hit: set random background stripes")
                elif event.key == pygame.K_RIGHT:
                    dx, dy = ScreenTouch.OFFSET
                    ScreenTouch.OFFSET = (dx + 0.1, dy)
                    print("RIGHT key hit: increase touch offset along x")
                elif event.key == pygame.K_LEFT:
                    dx, dy = ScreenTouch.OFFSET
                    ScreenTouch.OFFSET = (dx - 0.1, dy)
                    print("LEFT key hit: decrease touch offset along x")
                elif event.key == pygame.K_DOWN:
                    dx, dy = ScreenTouch.OFFSET
                    ScreenTouch.OFFSET = (dx, dy + 0.1)
                    print("DOWN key hit: increase touch offset along y")
                elif event.key == pygame.K_UP:
                    dx, dy = ScreenTouch.OFFSET
                    ScreenTouch.OFFSET = (dx, dy - 0.1)
                    print("UP key hit: decrease touch offset along y")
                elif event.key == pygame.K_KP_PLUS:
                    self.setImageSize(ScreenImage.SIZE + 10)
                    print("KP_PLUS key hit: increase image size")
                elif event.key == pygame.K_KP_MINUS:
                    self.setImageSize(ScreenImage.SIZE - 10)
                    print("KP_MINUS key hit: decrease image size")
                elif event.key == pygame.K_KP1:
                    self.setXYImage("KP0", 0, 0.25, 0.75)
                    print("KP0 key hit: place image (ID 1) accordingly")
                elif event.key == pygame.K_KP2:
                    self.setXYImage("KP2", 2, 0.5, 0.75)
                    print("KP2 key hit: place image (ID 2) accordingly")
                elif event.key == pygame.K_KP3:
                    self.setXYImage("KP3", 3, 0.75, 0.75)
                    print("KP3 key hit: place image (ID 3) accordingly")
                elif event.key == pygame.K_KP4:
                    self.setXYImage("KP4", 4, 0.25, 0.5)
                    print("KP4 key hit: place image (ID 4) accordingly")
                elif event.key == pygame.K_KP5:
                    self.setXYImage("KP5", 5, 0.5, 0.5)
                    print("KP5 key hit: place image (ID 5) accordingly")
                elif event.key == pygame.K_KP6:
                    self.setXYImage("KP6", 6, 0.75, 0.5)
                    print("KP6 key hit: place image (ID 6) accordingly")
                elif event.key == pygame.K_KP7:
                    self.setXYImage("KP7", 7, 0.25, 0.25)
                    print("KP7 key hit: place image (ID 7) accordingly")
                elif event.key == pygame.K_KP8:
                    self.setXYImage("KP8", 8, 0.5, 0.25)
                    print("KP8 key hit: place image (ID 8) accordingly")
                elif event.key == pygame.K_KP9:
                    self.setXYImage("KP9", 9, 0.75, 0.25)
                    print("KP9 key hit: place image (ID 9) accordingly")
                elif event.key == pygame.K_n:
                    self.manager.set_normal_mode()
                    print("N key hit: set normal mode")
                elif event.key == pygame.K_m:
                    self.manager.set_mouse_mode()
                    print("M key hit: set mouse mode")
                elif event.key == pygame.K_r:
                    self.manager.set_rat_mode()
                    print("R key hit: set rat mode")

            # Finger events (touchscreen)
            if event.type == pygame.FINGERDOWN:
                # event values are normalized to [0.0, 1.0]
                point = (event.x, event.y)
                point = self.manager.detector_area.area_to_screen(point)
                px_screen = self.manager.detector_area.screen_ratio_to_px(
                    point
                )
                point = self.manager.display_area.screen_to_area(point)
                touch = self.manager.add_touch(event.finger_id, point)
                print(f"finger down: add touch {touch.get_center()}")
                self.check_if_touch_on_image(touch, px_screen)

            if event.type == pygame.FINGERUP:
                self.manager.remove_touch(event.finger_id)
                self.send(f"finger up: {event.finger_id}")

    # Main loop
    # ----------------

    def step(self, fps: int = 30) -> bool:
        """Process one frame. Returns False when the app should quit."""
        self.process_commands()
        self.manager.render(fps=fps)
        return self.running

    def run(self, fps: int = 30) -> None:
        """Blocking event loop.  Calls quit() when done."""
        while self.running:
            try:
                self.step(fps=fps)
            except Exception:
                print(traceback.format_exc())
                self.running = False
            sleep(0.001)

    def quit(self) -> None:
        """Quit the application."""
        self.running = False
        self.manager.quit()
        if self.ser is not None:
            self.ser.close()
        pygame.quit()
        print("Quit TouchScreen")

    def get_keyboard_commands(self) -> list[str]:
        """Return a list of keyboard commands for testing purposes."""
        return [
            "Q / ESC: Quit",
            "C: Toggle calibration",
            "O: Clear display",
            "A: Remove all images",
            "I: Add random image at random position",
            "S: Add random stripes at random position",
            "B: Set random background color",
            "V: Set random background stripes",
            "KP_PLUS / KP_MINUS: Increase / decrease image size",
            "Arrow keys: Adjust touch offset (Left/Right/Up/Down)",
            "KP1..KP9: Place images in a 3x3 grid (IDs 1..9)",
            "Mouse click: Add simulated touch at click position",
            "Finger events: Touchscreen finger down / up",
            "N: Set normal mode",
            "M: Set mouse mode",
            "R: Set rat mode",
        ]


if __name__ == "__main__":
    TEST_MODE = False
    ts = TouchScreen(TEST_MODE)
    ts.load_all_images()
    if ts.ser is None:
        print("=== TEST MODE ===")
        for command in ts.get_keyboard_commands():
            print(command)

    # Setup adjustments
    # ----------------
    ts.setTouchOffset(0, 0)

    # Main loop
    # ----------------
    ts.run()
    ts.quit()
