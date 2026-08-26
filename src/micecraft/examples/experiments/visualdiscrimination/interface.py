"""
This code defines the visual application of a touchscreen experiment for mice,
where they are trained to discriminate between two images displayed on a
touchscreen. It is designed to work with the TouchScreenExperiment class
defined in exemple_touchscreen.py, and to visually represent the state of the
experiment, including the animals, their RFID, their current phase in the
experiment, and the touchscreen images they should be responding to. The
application also includes a context menu that allows the user to manually
change the state of the experiment, such as progressing an animal to the next
phase, changing the expected touchscreen image for an animal, or simulating
touchscreen events. The visual representation of the animals is done using
colored circles, and the application continuously updates to reflect changes in
the experiment state.

@author: xmousset
"""

from __future__ import annotations

import math
import time
import logging
import colorsys
import traceback
import threading
from typing import Callable, Literal

from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import QMenu, QWidget
from micecraft.soft.gui.WMouse import WMouse
from micecraft.soft.gui.WBlock import WBlock
from micecraft.devices.gate.gui.WGate import WGate
from micecraft.devices.waterpump.gui.WPump import WPump
from micecraft.devices.touchscreen.gui.WTouchScreen import WTouchScreen
from micecraft.soft.gui.VisualStorageAlarm import VisualStorageAlarm
from micecraft.devices.touchscreen.inPy.ts_img_manager import TSImage
from micecraft.examples.experiments.visualdiscrimination.experiment import (
    VisualDiscriminationExperiment,
)


class UserAction:
    """Class to link a callable action with its arguments and a log message.
    Used when user interacts with the interface."""

    def __init__(
        self,
        action: Callable,
        action_args: tuple = (),
        log: str | None = None,
    ) -> None:
        """Initialise the UserAction with the callable 'action', its arguments
        'args', and the log message 'log' to display when the action is
        executed."""
        self.action = action
        self.args = action_args
        self.log: str | None = log

    def exec(self):
        """Log if necessary and execute the callable 'action' with 'args' if
        the callable is not None."""
        msg = f"[user_action] name: {self.action.__name__} "
        if self.log is not None:
            msg += f"log: {self.log}"

        logging.info(msg)

        if self.action is not None:
            self.action(*self.args)


class VisualRoom:
    """Class to visually represent a room in the experiment, with its gate,
    block, and water pump. The rooms are stored in the class variable ALL, and
    can be retrieved by name using the get_from_name class method."""

    ALL: list[VisualRoom] = []

    @classmethod
    def get_from_name(cls, name: str) -> VisualRoom | None:
        """Get the VisualRoom object with the name 'name' in ALL."""
        for room in cls.ALL:
            if str(room) == name:
                return room
        return None

    def __init__(
        self,
        parent: QWidget | None,
        name: str,
        gate_pos: tuple[int, int],
        gate_touchscreen_direction: (
            str | Literal["top", "bottom", "left", "right"]
        ) = "right",
        flip_gate_AB: bool = False,
    ) -> None:
        self.parent = parent
        self.name: str = name

        gx, gy = gate_pos

        match gate_touchscreen_direction:
            case "right":
                bx, by = gx + 1, gy
                wpx, wpy = bx + 0.4, by - 0.4
                tsx, tsy = bx + 1.1, by + 0.5
                gate_angle = 0
                wp_angle = 0
                ts_angle = 90
            case "left":
                bx, by = gx - 1, gy
                wpx, wpy = bx + 0.4, by - 0.4
                tsx, tsy = bx - 0.1, by + 0.5
                gate_angle = 0
                wp_angle = 0
                ts_angle = -90
            case "top":
                bx, by = gx, gy - 1
                wpx, wpy = bx - 0.4, by
                tsx, tsy = bx + 0.5, by - 0.1
                gate_angle = -90
                wp_angle = -90
                ts_angle = 0
            case "bottom":
                bx, by = gx, gy + 1
                wpx, wpy = bx - 0.4, by
                tsx, tsy = bx + 0.5, by + 1.1
                gate_angle = -90
                wp_angle = -90
                ts_angle = 180
            case _:
                raise ValueError(
                    "Invalid gate_touchscreen_direction: "
                    f"{gate_touchscreen_direction!r}"
                )

        self.block = WBlock(bx, by, self.parent)
        self.block.setName(name + "_Block")

        if flip_gate_AB:
            gate_angle += 180
        self.gate: WGate = WGate(gx, gy, self.parent)
        self.gate.setName(name + "_Gate")
        self.gate.setAngle(gate_angle)

        self.wp: WPump = WPump(wpx, wpy, self.parent)
        self.wp.setName(name + "_WP")
        self.wp.setAngle(wp_angle)

        self.ts: WTouchScreen = WTouchScreen(tsx, tsy, ts_angle, self.parent)
        self.ts.setName(name + "_TS")

        VisualRoom.ALL.append(self)

    def bind_to_experiment(
        self,
        experiment: VisualDiscriminationExperiment,
        visual_listener: Callable,
    ):
        room = experiment.get_room(name=self.name)
        if room is None:
            logging.info(
                "[warning] [visual_room_binding] " f"wrong_name: {self.name} "
            )
            return
        self.gate.bindToGate(room.gate)
        room.gate.addDeviceListener(visual_listener)
        self.wp.bindToPump(room.wp)
        self.ts.bindToTouchScreen(room.ts)

    def __str__(self) -> str:
        return self.name


class VisualDiscriminationInterface(QWidget):

    refresher = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = "Visual experiment monitoring"
        self.shutting_down = False
        self.animals: list[WMouse] = []
        self.rooms: list[WBlock] = []
        self.painters: dict[str, QtGui.QPainter]
        self.visualStorageAlarm = None
        print("Starting...")

    def on_refresh_data(self):
        self.update()

    def monitor_GUI(self):
        while not self.shutting_down:
            self.refresher.emit()
            time.sleep(0.1)  # define the 'FPS' of application

    def listener(self, event):
        print(f"Event received: {event}")

    def shutdown(self):
        print("Exiting...")
        self.shutting_down = True
        self.experiment.shutdown_experiment()

    def init_house(
        self,
        size: tuple[int, int] = (1, 1),
        pos: tuple[int, int] = (0, 0),
    ):
        """Create a block widget house at 'block_pos'= [0, 0].

        Parameters
        ----------
        size : tuple[int, int], optional
            Define the number of blocks that compose the house (width, height).
            By default (1, 1).
        pos : tuple[int, int], optional
            Define the position of the house in the interface (x, y).
            By default (0, 0).
        """
        self.house = WBlock(pos[0], pos[1], self)  # relative to block size
        self.house.setSize(self.house.w * size[0], self.house.h * size[1])
        self.house.setName("Big House")

    def init_rooms(self):
        for room in VisualRoom.ALL:
            room.bind_to_experiment(self.experiment, self.listener)

    def create_animal(self):
        """Instanciate an animal into 'animal_list'"""
        number = len(self.animals) + 1
        animal_x = 140
        animal_y = 120 + ((number - 1) % 2 * 100)

        house_pos_available: tuple[int, int] = (
            int(self.house.w / 200),
            int(self.house.h / 200),
        )
        house_void = 2 * house_pos_available[0] * house_pos_available[1] - len(
            self.animals
        )

        if house_void > 0:
            found = False
            for x in range(house_pos_available[0]):
                for y in range(house_pos_available[1]):
                    if 2 * (x + 1) * (y + 1) > len(self.animals):
                        animal_x += x * 200
                        animal_y += y * 200
                        found = True
                        break
                if found:
                    break
        else:
            animal_x = int(self.animals[-1].x)
            animal_y = int(self.animals[-1].y) + 100

        animal = WMouse(animal_x, animal_y, self)
        animal.show()
        animal.number = number

        animal.vpos["home"] = (animal_x, animal_y)
        animal.vpos["target_location"] = (animal_x, animal_y)
        animal.vpos["location"] = (animal_x, animal_y)
        animal.vpos["inertia"] = (0, 0)

        self.animals.append(animal)

        for animal in self.animals:
            rgb = colorsys.hsv_to_rgb(
                animal.number / len(self.animals), 0.2, 1
            )
            animal.setBackgroundColor(
                int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
            )

    def get_all_rfid(self):
        """Get all RFID (visual only) in *self.animals*."""
        return [animal.rfid for animal in self.animals]

    def update_rfid(self):
        """Update the RFID of virtual animals with those from experiment."""
        expe_rfid_list = sorted(self.experiment.get_all_rfid())

        while len(expe_rfid_list) > len(self.get_all_rfid()):
            self.create_animal()

        visu_rfid_list = self.get_all_rfid()

        for expe_rfid in expe_rfid_list:
            if expe_rfid not in visu_rfid_list:
                i = 0
                while (
                    i < len(self.animals) and self.animals[i].rfid is not None
                ):
                    i += 1
                self.animals[i].rfid = expe_rfid

    def set_animal_target(self):
        """Set the target position in a room for smooth animal movement."""
        for animal in self.animals:
            rfid = animal.rfid

            if rfid is None:
                continue

            room = self.experiment.get_room(rfid_in=rfid)
            if room is None:
                animal.vpos["target_location"] = animal.vpos["home"]
                continue

            visual_room = VisualRoom.get_from_name(str(room))
            if visual_room is None:
                animal.vpos["target_location"] = animal.vpos["home"]
                continue

            animal.vpos["target_location"] = (
                visual_room.block.x + 40,  # type: ignore
                visual_room.block.y + 75,  # type: ignore
            )

    def get_pen(self) -> QtGui.QPainter:
        """Get the QPainter object with fixed parameters."""
        pen = QtGui.QPainter(self)
        pen.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        pen.setPen(QtGui.QPen(QtGui.QColor(50, 50, 50), 2))

        font = QtGui.QFont("Console")
        font.setPointSize(10)
        font.setBold(False)
        pen.setFont(font)

        return pen

    def paintEvent(self, event):  # type: ignore
        """Draw animal shape and information."""
        super().paintEvent(event)
        painter = self.get_pen()

        self.update_rfid()

        y_text = 20
        for rfid, animal in self.experiment.animals.items():

            text = f"{rfid}   |   {animal.phase}   |   " + "   |   ".join(
                animal.progression_display
            )

            painter.drawText(
                QtCore.QRect(10, y_text - 20, 600, y_text + 20),
                QtCore.Qt.AlignmentFlag.AlignCenter,
                text,
            )
            y_text += 15

        painter.drawText(
            QtCore.QRect(700, 0, 200, 40),
            QtCore.Qt.AlignmentFlag.AlignCenter,
            self.experiment.info.name,
        )

        if self.visualStorageAlarm is not None:
            self.visualStorageAlarm.draw(
                painter,
                textRect=QtCore.QRect(750, 320, 100, 50),
            )

        self.set_animal_target()

        for animal in self.animals:
            xt, yt = animal.vpos["target_location"]
            xc, yc = animal.vpos["location"]
            xi, yi = animal.vpos["inertia"]

            xa = xt - xc
            ya = yt - yc

            xa /= 1000
            ya /= 1000

            xi += xa
            yi += ya

            xi *= 0.9
            yi *= 0.9

            xc += xi
            yc += yi

            animal.vpos["location"] = (xc, yc)

            animal.move(int(xc), int(yc))
            animal.update()

        painter.end()

    def contextMenuEvent(self, event):  # type: ignore
        """Build the context menu and return (menu, action_map).
        action_map links each QtGui.QAction to a UserAction."""
        menu = QMenu(self)

        title = QtGui.QAction(self.name, menu)
        title.setDisabled(True)
        menu.addAction(title)

        action_map: dict[QtGui.QAction | None, UserAction] = {}

        menu.addSeparator()
        # rooms
        # ----------------
        title = QtGui.QAction("Rooms", menu)
        title.setDisabled(True)
        menu.addAction(title)

        # rooms re-initialisation
        menu_action = QtGui.QAction("re-initialise all hardware", menu)
        user_action = UserAction(self.experiment.init_experiment)
        user_action.log = "re-init all hardware"
        action_map[menu_action] = user_action
        menu.addAction(menu_action)

        # gate scale setting
        nb_rooms = len(self.experiment.get_all_rooms())
        for room in self.experiment.get_all_rooms():
            gate = room.gate
            room_menu = QMenu(str(room), menu)

            weight_menu = QMenu("gate expected weight", room_menu)

            power_ten = 10 ** int(math.log10(gate.mouseAverageWeight))
            weight_range = range(
                gate.mouseAverageWeight - power_ten,
                gate.mouseAverageWeight + power_ten,
                power_ten // 10,
            )

            for weight in weight_range:
                weight_action = QtGui.QAction(f"{weight} g", weight_menu)
                user_action = UserAction(room.set_animal_weight, (weight,))
                user_action.log = "expected weight modified"
                action_map[weight_action] = user_action
                if weight == gate.mouseAverageWeight:
                    weight_action.setCheckable(True)
                    weight_action.setChecked(True)
                weight_menu.addAction(weight_action)

            room_menu.addMenu(weight_menu)

            touch_action = QtGui.QAction("correct touch", room_menu)
            user_action = UserAction(room.simulate_ts_event, (True,))
            action_map[touch_action] = user_action
            room_menu.addAction(touch_action)

            touch_action = QtGui.QAction("wrong touch", room_menu)
            user_action = UserAction(room.simulate_ts_event, (False,))
            action_map[touch_action] = user_action
            room_menu.addAction(touch_action)

            display_action = QtGui.QAction("random display", room_menu)
            user_action = UserAction(room.ts_random_display, (TSImage.LIGHT,))
            action_map[display_action] = user_action
            room_menu.addAction(display_action)

            if nb_rooms > 1:
                menu.addMenu(room_menu)
            else:
                for action in room_menu.actions():
                    room_menu.removeAction(action)
                    menu.addAction(action)

        menu.addSeparator()
        # animals
        # ----------------
        title = QtGui.QAction("Animals", menu)
        title.setDisabled(True)
        menu.addAction(title)

        for rfid in self.experiment.get_all_rfid():
            rfid_menu = QMenu(rfid, menu)

            # go to next phase
            if rfid in self.experiment.animals.keys():
                menu_action = QtGui.QAction("proceed to next phase", rfid_menu)
                user_action = UserAction(
                    self.experiment.animals[rfid].proceed_to_next_phase
                )
                action_map[menu_action] = user_action
                rfid_menu.addAction(menu_action)

            # modify touchscreen image
            ts_image = self.experiment.get_ts_image(rfid)
            ts_img_menu = QMenu("set TouchScreen image", rfid_menu)
            for img in list(TSImage):
                menu_action = QtGui.QAction(img.name, ts_img_menu)
                user_action = UserAction(
                    self.experiment.set_ts_image, (rfid, img)
                )
                action_map[menu_action] = user_action
                if ts_image == img:
                    menu_action.setCheckable(True)
                    menu_action.setChecked(True)
                ts_img_menu.addAction(menu_action)

            rfid_menu.addMenu(ts_img_menu)
            menu.addMenu(rfid_menu)

        # menu execution
        # ----------------
        action = menu.exec(self.mapToGlobal(event.pos()))
        if action in action_map:
            action_map[action].exec()
        else:
            logging.info(f"[user_action] name: ACTION_CANCELED")

    def set_experiment(self, experiment: VisualDiscriminationExperiment):
        """Set the experiment for the interface."""
        self.experiment = experiment

    def start(self):
        """Start the application."""
        self.thread: threading.Thread = threading.Thread(  # type: ignore
            target=self.monitor_GUI
        )
        self.refresher.connect(self.on_refresh_data)
        self.thread.start()

        self.visualStorageAlarm = VisualStorageAlarm()
        self.raise_()


def excepthook(type_, value, traceback_):
    try:
        traceback.print_exception(type_, value, traceback_)
    except Exception:
        print(f"Exception: {type_.__name__}: {value}")
    QtCore.qFatal("")
