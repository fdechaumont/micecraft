"""
Created on 10 févr. 2025

@author: Fab
"""

from datetime import datetime
import numpy as np

import traceback
from micecraft.soft.device_event.DeviceEvent import DeviceEvent
from micecraft.devices.roomSensor.RoomSensor import RoomSensor


class RoomSensorDigest(object):
    
    def listener(self, event):
        d = {}
        for probe in self.probeList:
            val = self.roomSensor.getValue(probe)
            if val != None:
                d[probe] = val

        self.data.append(d)

        delay = (datetime.now() - self.start).total_seconds()
        if delay > self.delayS:
            self.start = datetime.now()

            resultDic = {}

            try:
                for probe in self.probeList:
                    values = []

                    for d in self.data:
                        if probe in d:
                            values.append(d[probe])

                    resultDic[f"mean {probe}"] = float(np.mean(values))
                    resultDic[f"std {probe}"] = float(np.std(values))
                    resultDic[f"max {probe}"] = float(np.max(values))
                    resultDic[f"min {probe}"] = float(np.min(values))

                self.fireEvent(
                    DeviceEvent(
                        "room sensor digest", self, str(resultDic), str(resultDic)
                    )
                )
            except:
                print("error in room sensor digest")
                traceback.print_exc()
            self.data = []

    def __init__(self, comPort, delayS=10):
        self.delayS = delayS
        self.data = []

        self.start = datetime.now()
        self.deviceListenerList = []

        self.probeList = [
            "Pressure",
            "Temperature",
            "Humidity",
            "r",
            "g",
            "b",
            "a",
            "Sound level",
            "Tilting x",
            "Tilting y",
            "Shock",
            "Raw accel x",
            "Raw accel y",
            "Raw accel z",
        ]

        self.comPort = comPort

        self.roomSensor = RoomSensor(comPort=self.comPort)
        self.roomSensor.addDeviceListener(self.listener)
        self.roomSensor.setDelaySampling(200, 20)

    def getProbeList(self):
        return self.probeList

    def shutdown(self):
        self.roomSensor.shutdown()

    def fireEvent(self, deviceEvent):
        for listener in self.deviceListenerList:
            listener(deviceEvent)

    def addDeviceListener(self, listener):
        self.deviceListenerList.append(listener)

    def removeDeviceListener(self, listener):
        self.deviceListenerList.remove(listener)

