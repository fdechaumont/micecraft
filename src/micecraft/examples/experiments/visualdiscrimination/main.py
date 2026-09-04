import sys

from PyQt6.QtWidgets import QApplication

from micecraft.devices.gate.Gate import Gate, GateOrder
from micecraft.devices.waterpump.WaterPump import WaterPump
from micecraft.devices.touchscreen.TouchScreen2 import TouchScreen2
from micecraft.devices.touchscreen.inPy.ts_img_manager import TSImage
from micecraft.soft.camera_recorder.CameraRecorder import CameraRecorder
from micecraft.devices.roomSensor.RoomSensorDigest import RoomSensorDigest
from micecraft.examples.experiments.visualdiscrimination.experiment import (
    VisualDiscriminationExperiment,
    Criteria,
    Phase,
    Room,
)
from micecraft.examples.experiments.visualdiscrimination.interface import (
    VisualDiscriminationInterface,
    VisualRoom,
    excepthook,
)


# ================ EXPERIMENT PARAMETERS ================
def define_experiment_parameters():

    # Images
    # ----------------
    images_to_attribute = [TSImage.PLANE, TSImage.FLOWER]

    # Phases creation
    # ----------------
    Phase.ALL = []

    Phase(
        "BLACK_WHITE",
        1,
        Criteria(min_rewards=10, min_trials=50),
        force_correct_image=TSImage.LIGHT,
    )
    Phase("FLOWER_PLANE", 2, Criteria(accuracy=(0.8, 50)))
    Phase("REVERSAL", 3, Criteria(accuracy=(0.8, 50)), use_opposite=True)
    Phase("END", 4, Criteria(), force_correct_image=TSImage.DARK)

    # Room creation
    # ----------------
    Room.ALL = []

    wp_alpha = WaterPump(comPort="COM0")
    ts_alpha = TouchScreen2(comPort="COM0")
    gate_alpha = Gate(
        COM_Servo="COM0",
        COM_Arduino="COM0",
        COM_RFID="COM0",
        weightFactor=0.6,
        mouseAverageWeight=25,
    )
    gate_alpha.setOrder(
        GateOrder.ONLY_ONE_ANIMAL_IN_B,
        options=["no rfid check on return"],
    )

    Room(
        name="rA",
        gate=gate_alpha,
        touchscreen=ts_alpha,
        waterpump=wp_alpha,
    )

    # Global recording
    # ----------------
    cam_recorder = None
    # cam_recorder = CameraRecorder(
    #     deviceNumber=0, bufferDurationS=50, showStream=True
    # )  # for saving videos

    sensors = None
    # sensors = RoomSensorDigest(
    #     comPort="COM29", delayS=5 * 60
    # )  # get environment data every 5 minutes

    # RETURN
    # ----------------
    return images_to_attribute, sensors, cam_recorder


def construct_app_visual(interface: VisualDiscriminationInterface):
    """Construct the visual representation of the experiment."""

    # get room names from the experiment in order of creation
    room_names = [room.name for room in interface.experiment.get_all_rooms()]

    VisualRoom(
        parent=interface,
        name=str(room_names[0]),
        gate_pos=(2, 0),
        gate_touchscreen_direction="right",
        flip_gate_AB=False,
    )

    interface.init_house(size=(2, 1))
    interface.init_rooms()

    interface.resize(1000, 400)
    interface.setWindowTitle("MiceCraft - Visual Discrimination Example")


if __name__ == "__main__":

    print("*** Start of program ***")
    experiment_parameters = define_experiment_parameters()

    sys.excepthook = excepthook
    app = QApplication([])

    interface = VisualDiscriminationInterface()
    app.aboutToQuit.connect(interface.shutdown)

    experiment = VisualDiscriminationExperiment(*experiment_parameters)
    interface.set_experiment(experiment)

    construct_app_visual(interface)

    interface.start()
    interface.show()

    sys.exit(app.exec())

    print("*** End of program ***")
