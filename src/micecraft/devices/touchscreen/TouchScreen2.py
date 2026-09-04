"""
Created on 4 oct. 2023

@author: Fab
"""

import sys
import random
import logging
import threading
from time import sleep
from random import randint
from typing import Callable

from micecraft.soft.com_manager.ComManager import ComManager
from micecraft.soft.device_event.DeviceEvent import DeviceEvent
from micecraft.devices.touchscreen.inPy.GrassHopper import GrassHopper
from micecraft.devices.touchscreen.ThreadTest import ThreadTest


class TouchScreen2:
    """
    notes:

    - The TTL levels of the raspberry UART are at 3.3v
    - Win 11 compatibility: PROLIFIC PL2303GC chip
    """

    def __init__(self, comPort, name="TouchScreen"):

        self.lock = threading.Lock()
        self.comPort = comPort
        self.name = name
        # self.connect()

        self.enabled = True
        self.deviceListenerList = []

        # self.communicationThread = threading.Thread(target=self.communication , name = f"TouchScreen Thread - {self.comPort}")
        # self.communicationThread.start()

        self.currentDisplay = []
        self.transparency = 255

        self.comManager = ComManager(
            comPort, self.comListener, "touchscreen com", 115200
        )
        self.comManager.enablePing()
        sleep(0.5)  # fixme with a check if connected

        self.comManager.send("config 3 1 350")
        self.displayCalibration = False

    def comListener(self, event):

        if not self.enabled:
            return
        serialString = event.description

        if "symbol xy touched" in serialString:
            try:
                data = serialString.split(" ")
                name = data[3]
                id = int(data[5])
                ratio = data[8].split(",")
                xr = float(ratio[0])
                yr = float(ratio[1])
                where = data[-1]
                w = where.split(",")
                x = int(float(w[0]))
                y = int(float(w[1]))
                xf = int(float(w[2]))
                yf = int(float(w[3]))
                self.fireEvent(
                    DeviceEvent(
                        "touchscreen",
                        self,
                        serialString,
                        (name, id, x, y, xf, yf, xr, yr),
                    )
                )
            except:
                self.log(
                    f"symbol xy touched : error in parse data: {serialString}"
                )

        if "missed" in serialString:
            try:
                data = serialString.split(" ")
                ratio = data[2].split(",")
                xr = float(ratio[0])
                yr = float(ratio[1])
                where = data[-1]
                w = where.split(",")
                xf = int(w[0])
                yf = int(w[1])
                self.fireEvent(
                    DeviceEvent(
                        "touchscreen", self, serialString, (xf, yf, xr, yr)
                    )
                )
            except:
                self.log(f"missed : error in parse data: {serialString}")

        if "traceback" in serialString:
            self.fireEvent(DeviceEvent("touchscreen", self, serialString))

    # ================ COMMANDS ================
    def setHello(self):
        self.send(f"hello")

    def ping(self):
        self.send("ping")

    def clear(self):
        """Clear all images, touches and background."""
        success = self.send("clear")
        if success:
            self.log("touchscreen clear")
            self.currentDisplay.clear()
            self.currentBg = None
        else:
            self.log(
                "touchscreen clear: send failed, not clearing local state"
            )

    def showCalibration(self, show: bool):
        if show:
            self.send("calibration show")
            self.displayCalibration = True
        else:
            self.send("calibration hide")
            self.displayCalibration = False

    def toggleCalibration(self):
        self.displayCalibration = not self.displayCalibration
        self.send("calibration toggle")

    def removeAllImages(self):
        self.send(f"removeAllImages")
        self.currentDisplay.clear()

    def setXYImage(
        self,
        name: str,
        id: int,
        centerX: float,
        centerY: float,
        rotation: float = 0.0,
        scale: float = 1.0,
        unit: str = "px",
    ):
        name = name.replace(" ", "_")
        d = "setXYImage"
        d += f" {name} {id} {centerX} {centerY} {rotation} {scale} {unit}"
        self.log(d)
        self.currentDisplay.append(
            {
                "name": name,
                "type": "xy_image",
                "id": id,
                "centerX": centerX,
                "centerY": centerY,
                "rotation": rotation,
                "scale": scale,
                "unit": unit,
            }
        )
        self.send(d)

    def removeXYImage(self, name: str):
        d = f"removeXYImage {name}"
        self.currentDisplay = [
            img for img in self.currentDisplay if img["name"] != name
        ]
        self.send(d)

    def setXYStripes(
        self,
        name: str,
        centerX: float,
        centerY: float,
        rotation: float = 0.0,
        scale: float = 1.0,
        stripe_angle: float = 0.0,
        thickness1: int = 10,
        thickness2: int = 10,
        color1: tuple[int, int, int] = (255, 255, 255),
        color2: tuple[int, int, int] = (0, 0, 0),
        unit: str = "px",
    ):
        name = name.replace(
            " ", "_"
        )  # if the name contains space, replace it by underscore
        d = f"setXYStripes {name} {centerX} {centerY} {rotation} {scale}"
        d += f" {stripe_angle} {thickness1} {thickness2}"
        d += f" {color1[0]},{color1[1]},{color1[2]}"
        d += f" {color2[0]},{color2[1]},{color2[2]}"
        d += f" {unit}"
        self.log(d)
        self.currentDisplay.append(
            {
                "name": name,
                "type": "xy_stripes",
                "centerX": centerX,
                "centerY": centerY,
                "rotation": rotation,
                "scale": scale,
                "stripe_angle": stripe_angle,
                "thickness1": thickness1,
                "thickness2": thickness2,
                "color1": color1,
                "color2": color2,
                "unit": unit,
            }
        )
        self.send(d)

    def removeXYStripes(self, name: str):
        d = f"removeXYStripes {name}"
        self.currentDisplay = [
            img for img in self.currentDisplay if img["name"] != name
        ]
        self.send(d)

    def removeImage(self, name: str):
        d = f"removeImage {name}"
        self.currentDisplay = [
            img for img in self.currentDisplay if img["name"] != name
        ]
        self.send(d)

    def moveImage(
        self,
        name: str,
        centerX: float,
        centerY: float,
        unit: str = "px",
    ):
        d = f"moveImage {name} {centerX} {centerY} {unit}"
        self.send(d)

    def setTransparency(self, transparency: float):
        """Set the transparency (0.0 - 1.0) of the touchscreen display."""
        transparency = int(transparency * 255)
        if transparency >= 0 and transparency <= 255:
            self.transparency = transparency
            self.send(f"transparency {self.transparency}")

    def setImageSize(self, imageSize: int | float, unit: str = "px"):
        self.send(f"imageSize {imageSize} {unit}")

    def setBgColor(self, color: tuple[int, int, int]):
        r, g, b = color
        self.send(f"setBgColor {r} {g} {b}")

    def setBgStripes(
        self,
        thickness1: int,
        thickness2: int,
        angle: float,
        color1: tuple[int, int, int],
        color2: tuple[int, int, int],
    ):
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        d = f"setBgStripes {thickness1} {thickness2} {angle} {r1} {g1} {b1} {r2} {g2} {b2}"
        self.log(d)
        self.send(d)

    def removeBg(self):
        d = f"removeBg"
        self.log(d)
        self.send(d)

    def setImageOffset(self, dx: int, dy: int, unit: str = "px"):
        self.send(f"setImageOffset {dx} {dy} {unit}")

    def setTouchOffset(self, dx: int, dy: int, unit: str = "px"):
        self.send(f"setTouchOffset {dx} {dy} {unit}")

    def setMouseMode(self):
        # the ir screen is rotated to match the screen viewport
        self.send("mouseMode")

    def setRatMode(self):
        # the ir screen is rotated to match the screen viewport
        self.send("ratMode")

    def setNormalMode(self):
        # no screen rotation
        self.send("normalMode")

    def setMode(
        self,
        display_size: tuple[float, float] = (1, 1),
        display_center: tuple[float, float] = (0.5, 0.5),
        display_rotation: float = 0,
        display_invert_axis: tuple[bool, bool] = (False, False),
        detector_size: tuple[float, float] = (1, 1),
        detector_center: tuple[float, float] = (0.5, 0.5),
        detector_rotation: float = 0,
        detector_invert_axis: tuple[bool, bool] = (False, False),
    ):
        d = f"setMode {display_size[0]} {display_size[1]}"
        d += f" {display_center[0]} {display_center[1]} {display_rotation}"
        d += f" {int(display_invert_axis[0])} {int(display_invert_axis[1])}"
        d += f" {detector_size[0]} {detector_size[1]}"
        d += f" {detector_center[0]} {detector_center[1]} {detector_rotation}"
        d += f" {int(detector_invert_axis[0])} {int(detector_invert_axis[1])}"
        self.log(d)
        self.send(d)

    def crash(self):
        # force a crash (exception) on the device to test traceback report
        self.send(f"crash")

    # ================ UTILS ================

    def isAlarmOn(self):
        if not self.comManager.alarmConnect.isAlarmOn():
            return "Device disconnected"
        return False

    def log(self, message):
        logging.info(f"[TouchScreen][{self.comPort}][{self.name}] {message}")

    def send(self, message: str) -> bool:
        """Send a message to the device and return True on success, False on failure."""
        try:
            return self.comManager.send(message)
        except Exception:
            # ensure we don't raise from send; log and return False
            self.log(f"send: exception while sending '{message}'")
            return False

    def fireEvent(self, deviceEvent: DeviceEvent):
        for listener in self.deviceListenerList:
            listener(deviceEvent)

    def addDeviceListener(self, listener: Callable[[DeviceEvent], None]):
        self.deviceListenerList.append(listener)

    def removeDeviceListener(self, listener: Callable[[DeviceEvent], None]):
        self.deviceListenerList.remove(listener)

    def __str__(self, *args, **kwargs):
        return "TouchScreen " + self.name + " " + self.comPort

    def shutdown(self):
        self.enabled = False
        self.comManager.shutdown()

    def getCurrentImageList(self):
        return self.currentDisplay


if __name__ == "__main__":
    COM_PORT = "COM4"

    logging.basicConfig(level=logging.INFO)
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    def listener(event):
        print(event)
        if "symbol xy touched" in event.description:
            name = event.data[0]
            print(f"symbol xy touched: name: {name}")

    print("Starting touchScreen test.")
    ts = TouchScreen2(COM_PORT)
    ts.addDeviceListener(listener)
    ts.setNormalMode()
    ts.clear()
    ts.setXYImage("TRUE", 29, 0.25, 0.5, unit="ratio")
    ts.setXYImage("FALSE", 30, 0.75, 0.5, unit="ratio")
    ts.setMouseMode()
    # ts.setRatMode()

    print("COMMAND: VARIABLES")
    print("------------------")
    print("z: force a crash on the device")
    print("g: grass hopper demo")
    print("t: thread test")
    print("a: send ping")
    print("0: true on left and false on right")
    print("1-9 <id>: put image on numpad coordinates")
    print("c: toggle calibration")
    print("i <id>: add one image at random position and rotation")
    print("m: <n, m, r>: normal, mouse or rat mode")
    print("o: clear screen")
    print("s <angle>: add one stripe image")
    print("b: add random background stripes")
    print("# <size>: set image size in pixels")
    print("q: quit")

    while True:
        command = input("command: ").strip()

        # ignore empty input
        if not command:
            continue

        # split into tokens and normalize the command letter to lowercase
        parts = command.split()

        cmd = parts[0].lower()
        arg = parts[1] if len(parts) == 2 else None

        if cmd == "q":
            ts.shutdown()
            break

        if cmd.isnumeric():
            ts.clear()
            if cmd == "0":
                ts.setXYImage("TRUE", 29, 0.25, 0.5, unit="ratio")
                ts.setXYImage("FALSE", 30, 0.75, 0.5, unit="ratio")
            else:
                if arg is None:
                    arg = "29"
                xs = [0.25, 0.5, 0.75]
                ys = [0.25, 0.5, 0.75]
                pos = int(cmd) - 1
                x = xs[pos % 3]
                y = ys[pos // 3]
                ts.setXYImage("NUMPAD", int(arg), x, y, unit="ratio")

        if cmd == "a":
            ts.ping()

        if cmd == "t":
            ThreadTest(ts)

        if cmd == "z":
            ts.crash()

        if cmd == "c":
            ts.toggleCalibration()

        if cmd == "i":
            if arg is None:
                idx = randint(0, 28)
            else:
                idx = int(arg)
            ts.removeXYImage("random_image")
            ts.setXYImage(
                "random_image",
                idx,
                random.random(),
                random.random(),
                random.random() * 360,
                random.random() + 0.5,
                "ratio",
            )

        if cmd == "m":
            if arg is None:
                print("Please specify mode: n (normal), m (mouse), r (rat)")
                continue
            if arg.lower() == "n":
                ts.setNormalMode()
            elif arg.lower() == "m":
                ts.setMouseMode()
            elif arg.lower() == "r":
                ts.setRatMode()

        if cmd == "g":
            GrassHopper(ts)

        if cmd == "o":
            ts.clear()

        if cmd == "s":
            if arg is None:
                angle = randint(-90, 90)
            else:
                angle = float(arg)
            ts.removeXYStripes("random_stripes")
            ts.setXYStripes(
                name="random_stripes",
                centerX=round(random.random(), 2),
                centerY=round(random.random(), 2),
                stripe_angle=angle,
                thickness1=randint(1, 30),
                unit="ratio",
            )

        if cmd == "b":
            ts.setBgStripes(
                thickness1=randint(5, 20),
                thickness2=randint(5, 20),
                angle=randint(-90, 90),
                color1=(randint(0, 255), randint(0, 255), randint(0, 255)),
                color2=(randint(0, 255), randint(0, 255), randint(0, 255)),
            )

        if cmd == "#":
            if arg is None:
                print("Please specify size value.")
                continue
            size = int(arg)
            ts.setImageSize(size, unit="px")
            # ts.setImageSize(0.5, unit="ratio")

    # exit loop cleanly
    sys.exit(0)
