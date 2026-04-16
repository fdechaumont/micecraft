"""Test the room sensor block.

Created on 27 mars 2024

@author: Fab
"""

from time import sleep
from micecraft.devices.roomSensor.RoomSensor import RoomSensor

if __name__ == "__main__":

    def listener(event):
        print("-------- data from sensor:")
        print("shock:", roomSensor.getShock())
        print("pressure: ", roomSensor.getPressure())
        print("temperature: ", roomSensor.getTemperature())
        print("humidity %: ", roomSensor.getHumidity())

        print("ambient red light : ", roomSensor.getRedLight())
        print("ambient green light: ", roomSensor.getGreenLight())
        print("ambient blue light: ", roomSensor.getBlueLight())
        print("ambient global light: ", roomSensor.getAmbientLight())

        print("sound level: ", roomSensor.getSoundLevel())
        print("titling x: ", roomSensor.getTiltingX())
        print("titling y: ", roomSensor.getTiltingY())

        print("accel x: ", roomSensor.getValue("Raw accel x"))
        print("accel y: ", roomSensor.getValue("Raw accel y"))
        print("accel z: ", roomSensor.getValue("Raw accel z"))

    roomSensor = RoomSensor(comPort="/dev/ttyACM0")
    roomSensor.addDeviceListener(listener)
    roomSensor.setDelaySampling(200, 20)

    input("hit enter to stop")
    roomSensor.shutdown()
