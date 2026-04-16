"""Room sensor code.

Created on 10 mars 2022

@author: Fab
"""

import copy
import logging
from time import sleep
from micecraft.soft.com_manager.ComManager import ComManager
from micecraft.soft.device_event.DeviceEvent import DeviceEvent



class RoomSensor:
    # Threaded version

    def __init__(self, comPort: str = "COM17", name: str = "RoomSensor") -> None:
        self.name = name
        self.comPort = comPort

        self.nbRight = 0
        self.nbLeft = 0

        self.enabled = True
        self.data = {}  # current data
        self.previous = {}  # previous data
        self.delta = {}  # difference between data and previous

        self.deviceListenerList = []

        self.comManager = ComManager(
            self.comPort, self.comListener, alarmName="Room sensor"
        )
        sleep(0.5)  # to start up the device and be ready to receive commands.

    def shutdown(self) -> None:
        self.enabled = False
        self.comManager.shutdown()

    def comListener(self, event):
        if self.enabled:
            serialString = event.description

            if "end" in serialString:
                message = ""
                for k, v in self.data.items():
                    message += f"{k}:{v};"
                self.fireEvent(
                    DeviceEvent(
                        "RoomSensor", self, message, data=copy.deepcopy(self.data)
                    )
                )

            if ":" in serialString:
                try:
                    s = serialString.split(":")
                    k = s[0]
                    v = s[1]

                    if k in self.data:
                        self.previous[k] = self.data[k]

                    self.data[k] = float(v)

                    if k in self.previous and self.previous[k] is not None:
                        self.delta[k] = self.data[k] - self.previous[k]

                except:
                    logging.error("RoomSensor reading: %s", serialString)

    def log(self, message: str):
        logging.info("RoomSensor: %s %s %s", self.name, self.comPort, message)

    def getValue(self, name: str) -> float:
        if name in self.data:
            return self.data[name]
        return None

    def getPressure(self) -> float:
        return self.getValue("Pressure")

    def getTemperature(self) -> float:
        return self.getValue("Temperature")

    def getHumidity(self) -> float:
        return self.getValue("Humidity")

    def getRedLight(self) -> float:
        return self.getValue("r")

    def getGreenLight(self) -> float:
        return self.getValue("g")

    def getBlueLight(self) -> float:
        return self.getValue("b")

    def getAmbientLight(self) -> float:
        return self.getValue("a")

    def getSoundLevel(self) -> float:
        return self.getValue("Sound level")

    def getTiltingX(self) -> float:
        return self.getValue("Tilting x")

    def getTiltingY(self) -> float:
        return self.getValue("Tilting y")

    def getShock(self) -> float:
        return self.getValue("Shock")

    def send(self, message: str):
        self.comManager.send(message)

    def setDelaySampling(self, delay: float = 200.0, nbShockSampling: int = 20):
        self.send(f"delay:{delay}")
        self.send(f"nbShockSampling:{nbShockSampling}")

    def fireEvent(self, deviceEvent):
        for listener in self.deviceListenerList:
            listener(deviceEvent)

    def addDeviceListener(self, listener):
        self.deviceListenerList.append(listener)

    def removeDeviceListener(self, listener):
        self.deviceListenerList.remove(listener)

    def __str__(self, *args, **kwargs) -> str:
        return self.name
