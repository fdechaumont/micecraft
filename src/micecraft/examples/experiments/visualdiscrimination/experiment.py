"""
This code defines a touchscreen experiment for mice, where they are trained to
discriminate between two images displayed on a touchscreen. The experiment is
structured in phases, with specific criteria for progression. The code includes
classes for managing the experiment parameters, mouse data, and the experiment
itself, as well as methods for handling hardware interactions and recording
trial outcomes.
"""

import os
import sys
import logging
from pathlib import Path
from random import shuffle
from threading import Timer
from typing import Any, Callable
from datetime import datetime, timedelta

from micecraft.devices.gate.Gate import Gate, GateOrder
from micecraft.devices.waterpump.WaterPump import WaterPump
from micecraft.devices.touchscreen.TouchScreen2 import TouchScreen2
from micecraft.devices.roomSensor.RoomSensorDigest import RoomSensorDigest
from micecraft.soft.utils.WaitForAllThreads import WaitForAllThreads
from micecraft.soft.device_event.DeviceEvent import DeviceEvent
from micecraft.soft.utils.ParameterSaver import ParameterSaver
from PyQt6.QtWidgets import QInputDialog, QMessageBox

from micecraft.soft.camera_recorder.CameraRecorder import (
    CameraRecorder,
    CRText,
)
from micecraft.devices.touchscreen.inPy.ts_img_manager import TSImage


class ExperimentSettings:
    """Class that handle the identification of the experiment, with its name
    and comment.
    It also handle the saving and loading of the previous experiment name, and
    ask the user if they want to reload it.
    """

    def __init__(self):
        """Initialise the experiment name, with loading and saving of the
        previous experiment name."""
        script_path = Path(__file__).parent
        self.settings_saver = ParameterSaver(
            str(script_path), "previous_experiment"
        )
        self.reset_experiment()
        self.load_previous_experiment()

    def start_experiment(self):
        """Start the experiment by asking the user if they want to reload the
        previous experiment, and if not, ask them to input the experiment name
        and comment."""
        self.user_settings_selection()
        self.save_experiment()

    def reset_experiment(self):
        """Reset the experiment name and comment."""
        self.name: str = ""
        self.comment: str = ""
        self.auto_random_attribution: bool = True

    def user_settings_selection(self):
        """Ask the user if they want to reload the previous experiment,
        if it exists."""

        if self.name == "":
            reload = False
        else:
            btn = QMessageBox.question(
                None,
                "Reload experiment",
                f"Reload previous experiment '{self.name}'?",
            )
            reload = btn == QMessageBox.StandardButton.Yes

        if reload:
            self.comment += " (reloaded)"
        else:
            self.user_input_identification()
            self.ask_user_image_assignment()

    def ask_user_image_assignment(self):
        """Ask the user whether to assign TSImage at random during experiment
        or to wait until the user assigns them manually."""
        btn = QMessageBox.question(
            None,
            "Image assignment",
            "Assign animals image at random?",
        )
        self.auto_random_attribution = btn == QMessageBox.StandardButton.Yes

    def save_experiment(self):
        """Save the experiment name and comment for the next session."""
        data_to_save = {
            "experiment_name": self.name,
            "experiment_comment": self.comment,
            "random_assignment": self.auto_random_attribution,
        }
        self.settings_saver.setData(data_to_save)

    def load_previous_experiment(self):
        """Load the previous experiment name and comment, if they exist."""
        exp_name = self.settings_saver.getValue("experiment_name")
        if exp_name is not None and isinstance(exp_name, str):
            self.name = exp_name

        exp_comment = self.settings_saver.getValue("experiment_comment")
        if exp_comment is not None and isinstance(exp_comment, str):
            self.comment = exp_comment

        random_attr = self.settings_saver.getValue("random_assignment")
        if random_attr is not None and isinstance(random_attr, bool):
            self.auto_random_attribution = random_attr

    def user_input_identification(self):
        """Ask the user to input the experiment name and comment."""
        while True:
            name, ok = QInputDialog.getText(
                None, "Experiment ID", "Enter the id for this experiment:"
            )
            if not ok:
                continue
            if name is None or name.strip() == "":
                QMessageBox.warning(
                    None, "Invalid ID", "Experiment ID cannot be empty."
                )
                continue
            break
        self.name = name.replace("-", "_")
        self.comment, _ = QInputDialog.getText(
            None, "Experiment comment", "Experiment comments:"
        )


class Phase:
    """Object that handle the phases for an animal during the experiment."""

    ALL: list[Phase] = []

    @classmethod
    def get(cls, id: int | str) -> Phase:
        """Get a Phase object by its name or order."""
        name = None
        order = None

        if isinstance(id, int):
            order = id
        if isinstance(id, str):
            name = id

        for phase in cls.ALL:
            if name and phase.name == name:
                return phase
            if order and phase.order == order:
                return phase
        raise ValueError(f"Phase ID '{id}' ({type(id)}) not found.")

    @classmethod
    def get_first(cls) -> Phase:
        """Get the first Phase object based on order."""
        if not cls.ALL:
            raise ValueError("No phases available.")
        return min(cls.ALL, key=lambda phase: phase.order)

    @classmethod
    def get_last(cls) -> Phase:
        """Get the last Phase object based on order."""
        if not cls.ALL:
            raise ValueError("No phases available.")
        return max(cls.ALL, key=lambda phase: phase.order)

    def __init__(
        self,
        name: str,
        order: int,
        criteria: Criteria,
        force_correct_image: TSImage | None = None,
        use_opposite: bool = False,
    ) -> None:
        """Initialise a Phase object with a name and its criteria completion
        as optional keyword arguments.

        Parameters
        ----------
        name : str
            Name of the phase, used for display and identification. Must be
            unique among all phases.
        order : int
            Order of the phase, used for ordering all phases. The lower the
            order, the earlier the phase. Must be unique among all phases.
        criteria : Criteria
            Criteria for phase completion.
        force_correct_image : TSImage | None, optional
            The correct image for the phase (no matter which correct image
            was attributed to the animals). If None, use the image attributed
            to the animal. None by default.
        use_opposite : bool, optional
            Whether to use the opposite image as the correct one during this
            phase (see `Animal.get_correct_image()` method). False by default.
        """

        for phase in Phase.ALL:
            if phase.name == name:
                raise ValueError(f"Phase name '{name}' already exists.")
            if phase.order == order:
                raise ValueError(f"Phase order '{order}' already exists.")

        self.name: str = name.replace("-", "_")
        self.order: int = order
        self.criteria: Criteria = criteria
        self.force_correct_image: TSImage | None = force_correct_image
        self.use_opposite: bool = use_opposite

        Phase.ALL.append(self)
        Phase.ALL.sort(key=lambda p: p.order)

    def __str__(self) -> str:
        return f"{Phase.ALL.index(self):02d}-{self.name}"

    def next(self) -> Phase:
        """Proceed to the next phase in declaration order."""
        idx = Phase.ALL.index(self)
        if idx == len(Phase.ALL) - 1:
            return self
        else:
            return Phase.ALL[idx + 1]

    def previous(self) -> Phase:
        """Return the previous phase in declaration order."""
        idx = Phase.ALL.index(self)
        if idx > 0:
            return Phase.ALL[idx - 1]
        else:
            return self


class Criteria:
    """Object that handle the criteria for a mouse to complete a phase.
    The animal must have, at least, those criteria to complete the phase."""

    @classmethod
    def from_repr(cls, repr: str):
        """Initialise a Criteria object from its string representation."""
        raw = repr.split("_")
        return cls(
            min_rewards=int(raw[0]),
            min_trials=int(raw[1]),
            accuracy=(float(raw[2]), int(raw[3])),
        )

    def __init__(
        self,
        min_rewards: int = 0,
        min_trials: int = 0,
        accuracy: tuple[float, int] = (0.0, 0),
    ) -> None:
        """Initialise a Criteria object with the criteria as optional keyword arguments.

        Parameters
        ----------
        min_rewards : int, optional
            Minimum number of rewards an animal needs to pick up, by default 0.
        min_trials : int, optional
            Minimum number of trials an animal needs to take, by default 0.
        accuracy : tuple of (float, int), optional
            Minimum accuracy needed over the last N trials (accuracy, N), by default (0.0, 0).
        """
        if min_rewards < 0:
            raise ValueError("'min_rewards' must be a positive integer.")
        if min_trials < 0:
            raise ValueError("'min_trials' must be a positive integer.")
        if accuracy[0] < 0 or accuracy[0] > 1:
            raise ValueError("'accuracy[0]' must be in [0,1].")
        if accuracy[1] < 0:
            raise ValueError("'accuracy[1]' must be a positive integer.")

        self.rewards: int = min_rewards
        """Minimum number of rewards an animal needs to pick up."""
        self.trials: int = min_trials
        """Minimum number of trials an animal needs to take."""
        self.accuracy: tuple[float, int] = accuracy
        """Minimum accuracy needed over the last N trials (accuracy, N)."""

    def __str__(self) -> str:
        str_repr = [
            self.rewards,
            self.trials,
            self.accuracy[0],
            self.accuracy[1],
        ]
        str_repr = map(str, str_repr)
        return "_".join(str_repr)

    def is_fulfilled(self, animal: Animal) -> bool:
        """Check if an animal has completed the criteria."""
        if self.rewards > 0:
            rewards_list = animal.get_rewards(animal.phase)
            if sum(rewards_list.values()) < self.rewards:
                return False

        if self.trials > 0 or self.accuracy[1] > 0:
            trials_list = animal.get_trials(animal.phase)
            if len(trials_list) < self.trials:
                return False
            if len(trials_list) < self.accuracy[1]:
                return False
            if self.accuracy[0] > 0:
                last_results = list(trials_list.values())[-self.accuracy[1] :]
                accuracy = sum(last_results) / len(last_results)
                if accuracy < self.accuracy[0]:
                    return False
        return True

    def get_progression(self, animal: Animal) -> list[str]:
        """Return a list containing all information regarding criteria
        progression."""
        progress_list = []

        if self.rewards > 0:
            rewards_list = animal.get_rewards(animal.phase)
            rewards_taken = sum(rewards_list.values())
            if rewards_taken < self.rewards:
                progress_list.append(
                    f"rewards: {rewards_taken}/{self.rewards} "
                    f"({rewards_taken / self.rewards * 100:.0f}%)"
                )

        trials = animal.get_trials(animal.phase)

        if self.trials > 0:
            if len(trials) < self.trials:
                progress_list.append(
                    f"trials: {len(trials)}/{self.trials} "
                    f"({len(trials) / self.trials * 100:.0f}%)"
                )

        if self.accuracy[1] > 0:
            if len(trials) < self.accuracy[1]:
                progress_list.append(
                    f"need {self.accuracy[1] - len(trials)} more trials for "
                    f"accuracy ({(len(trials) / self.accuracy[1]) * 100:.0f}%)"
                )
            else:
                last_results = list(trials.values())[-self.accuracy[1] :]
                accuracy = sum(last_results) / len(last_results)
                progress_list.append(f"accuracy: {accuracy * 100:.0f}%")

        if not progress_list:
            progress_list = ["Phase completed."]

        return progress_list


class Animal:
    """Animal object for MiceCraft experiment."""

    def __str__(self) -> str:
        """Return the RFID of the animal."""
        return self.rfid

    def __init__(self, rfid: str):
        """
        Initialise an Animal object for the experiment.

        Parameters
        ----------
        rfid : str
            Unique identifier (RFID) for the animal.
        """
        self.rfid: str = rfid
        self.full_description: str = ""
        self.correct_image: TSImage = TSImage.LIGHT
        """Touchscreen image attributed to the animal."""
        self.phase: Phase = Phase.get_first()
        """Current phase of the animal."""

        self.phases_start_time: dict[Phase, datetime] = {
            self.phase: datetime.now()
        }
        """Dict with Phase keys and datetime values of the start time of each
        phase."""
        self.phases_success_time: dict[Phase, datetime] = {}
        """Dict with Phase keys and datetime values of the success time of each
        phase."""
        self.trials_dic: dict[datetime, bool] = {}
        """Dict with datetime keys when animal performs a trial,
        True= success, False= fail."""
        self.touch_left_dic: dict[datetime, bool] = {}
        """Dict with datetime keys when touchscreen is touched meaningfully,
        True= touch left, False= touch right."""
        self.rewards_dic: dict[datetime, bool] = {}
        """Dict with datetime keys when a reward is delivered,
        True= reward picked, False= reward not picked."""

        self.progression_display: list[str] = ["not started yet"]
        """List describing current criteria progression."""

    @staticmethod
    def datetime_to_str(date: datetime):
        """Transform a datetime object into str (used in 'save_to_dict')."""
        return date.strftime("%Y/%m/%d, %H:%M:%S")

    @staticmethod
    def str_to_datetime(date: str):
        """Transform a str into datetime object (used in 'from_dict')."""
        return datetime.strptime(date, "%Y/%m/%d, %H:%M:%S")

    def save_as_dict(self) -> dict[str, Any]:
        """Save mouse data in a dict for further JSON save.

        Returns
        -------
        dict
            A JSON savable dictionnary.
        """
        dic = {}
        dic["rfid"] = self.rfid
        dic["full_description"] = self.full_description
        dic["ts_image"] = str(self.correct_image)
        dic["phase"] = str(self.phase)
        dic["criteria"] = str(self.phase.criteria)

        dic["phases_start_time"] = {
            str(phase): self.datetime_to_str(date)
            for phase, date in self.phases_start_time.items()
        }

        dic["phases_success_time"] = {
            str(phase): self.datetime_to_str(date)
            for phase, date in self.phases_success_time.items()
        }

        dic["trials_dic"] = {
            self.datetime_to_str(date): result
            for date, result in self.trials_dic.items()
        }

        dic["touch_left_dic"] = {
            self.datetime_to_str(date): result
            for date, result in self.touch_left_dic.items()
        }

        dic["rewards_picked"] = {
            self.datetime_to_str(date): result
            for date, result in self.rewards_dic.items()
        }

        return dic

    @classmethod
    def load_from_dict(cls, dic: dict[str, Any]) -> Animal:
        """Load mouse data from a previously saved dictionary.

        Parameters
        ----------
        dic : dict
            Dictionary containing the saved attributes needed to recreate a
            Mouse instance.
        """
        instance = cls(dic["rfid"])
        instance.full_description = dic["full_description"] + " (reloaded)"
        instance.correct_image = TSImage[dic["ts_image"]]
        _, phase_name = dic["phase"].split("-")
        instance.phase = Phase.get(phase_name)
        if str(instance.phase.criteria) != dic["criteria"]:
            raise ValueError(
                f"Criteria mismatch for phase '{instance.phase}': "
                f"saved '{dic['criteria']}', "
                f"current '{instance.phase.criteria}'."
            )

        instance.phases_start_time = {
            Phase.get(phase.split("-")[1]): cls.str_to_datetime(date)
            for phase, date in dic["phases_start_time"].items()
        }

        instance.phases_success_time = {
            Phase.get(phase.split("-")[1]): cls.str_to_datetime(date)
            for phase, date in dic["phases_success_time"].items()
        }

        instance.trials_dic = {
            cls.str_to_datetime(date): result
            for date, result in dic["trials_dic"].items()
        }

        instance.touch_left_dic = {
            cls.str_to_datetime(date): result
            for date, result in dic["touch_left_dic"].items()
        }

        instance.rewards_dic = {
            cls.str_to_datetime(date): result
            for date, result in dic["rewards_picked"].items()
        }

        instance.progression_display = instance.phase.criteria.get_progression(
            instance
        )

        return instance

    def add_trial(self, result: bool):
        """Save a trial datetime and its outcome in 'trials_dic'.
        Do not use this function if there is no result to save
        (for example if the trial was not completed)."""
        self.trials_dic[datetime.now()] = result
        self.progression_display = self.phase.criteria.get_progression(self)

    def add_side_touch(self, touch_left: bool):
        """Save a side touch in 'touch_left_dic', True if left, False
        otherwise."""
        self.touch_left_dic[datetime.now()] = touch_left

    def add_reward_search(self, picked: bool):
        """Save a reward search in 'rewards_dic', True if reward picked, False
        if no reward was available."""
        self.rewards_dic[datetime.now()] = picked
        self.progression_display = self.phase.criteria.get_progression(self)

    def proceed_to_next_phase(self):
        """Updates animal data to initialise next phase."""
        time = datetime.now()

        self.phases_success_time[self.phase] = time
        self.phase = self.phase.next()
        self.phases_start_time[self.phase] = time

    def get_trials(self, phase: Phase) -> dict[datetime, bool]:
        """Get all trials corresponding to specified phase."""
        if phase not in self.phases_start_time:
            return {}

        start_time = self.phases_start_time[phase]
        end_time = self.phases_success_time.get(phase, datetime.max)

        trials_filtered = {
            date: result
            for date, result in self.trials_dic.items()
            if start_time <= date and date <= end_time
        }

        return trials_filtered

    def get_rewards(self, phase: Phase) -> dict[datetime, bool]:
        """Get all rewards picked datetime corresponding to animal phase."""

        if phase not in self.phases_start_time:
            return {}

        start_time = self.phases_start_time[phase]
        end_time = self.phases_success_time.get(phase, datetime.max)

        rewards_filtered = {
            date: result
            for date, result in self.rewards_dic.items()
            if start_time <= date and date <= end_time
        }

        return rewards_filtered

    def phase_completed(self) -> bool:
        """Check if an animal has completed its phase criterias."""
        return self.phase.criteria.is_fulfilled(self)

    def get_correct_image(self) -> TSImage:
        """Get the correct image for the animal in its current phase."""
        if self.phase.force_correct_image is not None:
            correct_image = self.phase.force_correct_image
        else:
            correct_image = self.correct_image

        if self.phase.use_opposite:
            correct_image = correct_image.get_opposite()

        return correct_image


class Room:
    """Class for managing room logic and devices."""

    ALL: list[Room] = []

    @classmethod
    def get_from_name(cls, name: str) -> Room | None:
        """Get a room by its name or by the name of one of its devices."""
        if not cls.ALL:
            return None
        room_name = name.split("-")[0]
        for room in cls.ALL:
            if str(room) == room_name:
                return room
        return None

    @classmethod
    def get_from_rfid_in(cls, rfid: str | None) -> Room | None:
        """Get the room where the RFID is currently in."""
        if rfid is None:
            return None
        for room in cls.ALL:
            animal = room.animal_in
            if animal is not None and animal.rfid == rfid:
                return room
        return None

    def __init__(
        self,
        name: str,
        gate: Gate,
        touchscreen: TouchScreen2,
        waterpump: WaterPump,
    ):
        """Initialise a room with its name and devices."""
        for room in Room.ALL:
            if room.name == name:
                raise ValueError(f"Room name '{name}' already exists.")

        self.name: str = name.replace("-", "_")
        """Name of the room, used for display and identification. Must be
        unique among all rooms."""

        self.state: str = "EXIT"
        """State of the room, reflecting the animal's actions."""

        self.animal_in: Animal | None = None
        """Animal currently in the room, None if no animal."""

        self.expe_data_saver: Callable[[bool, bool], None] | None = None
        """Function to call to save all experiment data (not just room data).
        Used after each trial outcome."""

        self.video_recorder: Callable[[Animal, bool], None] | None = None
        """Function to call to record a video of the animal."""

        self.running_timers: list[Timer] = []
        """List of currently running timers."""

        self.gate: Gate = gate
        self.gate.name = self.name + "-" + "Gate"
        self.ts: TouchScreen2 = touchscreen
        self.ts.name = self.name + "-" + "TS"
        self.wp: WaterPump = waterpump
        self.wp.name = self.name + "-" + "WP"

        self.gate_listener: Callable | None = None

        Room.ALL.append(self)

    def __str__(self) -> str:
        """Return the name of the room."""
        return self.name

    def set_gate_listener(self, listener: Callable):
        """Set the gate listener."""
        self.gate_listener = listener
        self.init_room()

    def init_room(self, display_log: bool = True):
        """Initialise all hardware of the room."""

        # gate
        # ----------------
        if (
            self.gate_listener is not None
            and self.gate_listener not in self.gate.deviceListenerList
        ):
            self.gate.addDeviceListener(self.gate_listener)
        self.gate.setSpeedAndTorqueLimits(140, 140)
        self.gate.weightFactor = 0.6  # type: ignore
        if display_log:
            logging.info(
                "[init_hardware] "
                f"device: {self.gate.name} "
                f"COM_SERVO: {self.gate.COM_Servo} "
                f"COM_ARDUINO: {self.gate.COM_Arduino} "
                f"COM_RFID: {self.gate.COM_RFID} "
            )

        # touchscreen
        # ----------------
        if self.touchscreen_listener not in self.ts.deviceListenerList:
            self.ts.addDeviceListener(self.touchscreen_listener)
        # self.ts.setTransparency(0.5)
        self.ts.setMouseMode()
        self.ts.setImageSize(0.45, "ratio")
        self.ts.clear()
        self.ts.showCalibration(False)
        if display_log:
            logging.info(
                "[init_hardware] "
                f"device: {self.ts.name} "
                f"COM_PORT: {self.ts.comPort} "
            )

        # waterpump
        # ----------------
        if self.waterpump_listener not in self.wp.deviceListenerList:
            self.wp.addDeviceListener(self.waterpump_listener)
        self.wp.setDropParameters(255, 17, 0.025)
        if display_log:
            logging.info(
                "[init_hardware] "
                f"device: {self.wp.name} "
                f"COM_PORT: {self.wp.comPort} "
            )

    def log_animal_in_error(self, function: str):
        """Log a warning if no animal is in the room."""
        logging.info(
            "[warning] [animal_in] "
            f"room: {str(self)} "
            f"rfid: NOT_FOUND "
            f"callable: {function} "
        )

    def touchscreen_listener(self, event: DeviceEvent):
        """Function called by the touchscreen when it fires an event."""
        logging.debug(f"[touchscreen_event] event: {event.description} ")

        if not self.ts.enabled:
            logging.info(
                "[warning] [touchscreen_event] "
                f"room: {str(self)} "
                f"touchscreen: DISABLED "
            )
            return

        animal = self.animal_in
        if animal is None:
            self.log_animal_in_error("touchscreen_listener")
            return

        if "symbol xy touched" in event.description:
            # data: name, id, x, y, xf, yf
            if event.data is not None:
                img_name = event.data[0]
                img_id = event.data[1]
                img_x = event.data[2]
                img_y = event.data[3]
                touch_x = event.data[4]
                touch_y = event.data[5]
                logging.info(
                    f"[useful_touch] room: {str(self)} "
                    f"rfid: {animal} "
                    f"image_name: {img_name} "
                    f"image_id: {img_id} "
                    f"image_x: {img_x} "
                    f"image_y: {img_y} "
                    f"touch_x: {touch_x} "
                    f"touch_y: {touch_y} "
                )

            correct_image = animal.phase.force_correct_image
            if correct_image is None:
                correct_image = animal.correct_image
            if animal.phase.use_opposite:
                correct_image = correct_image.get_opposite()

            if correct_image == TSImage.ERROR:
                logging.info(
                    f"[warning] [trial_result] room: {str(self)} "
                    f"rfid: {animal} "
                    f"attribution: {str(animal.correct_image)} "
                    f"phase: {str(animal.phase)} "
                    f"info: user must assign an image "
                )
                return

            # choosen side
            # ----------------
            choice_str = "side_unknown"
            if "left_image" in event.description:
                choice_str = "left"
                animal.add_side_touch(touch_left=True)

            if "right_image" in event.description:
                choice_str = "right"
                animal.add_side_touch(touch_left=False)

            # correct answer
            # ----------------
            if str(correct_image) in event.description:
                logging.info(
                    f"[trial_result] room: {str(self)} "
                    f"rfid: {animal} "
                    f"attribution: {str(animal.correct_image)} "
                    f"phase: {str(animal.phase)} "
                    f"solution: {str(correct_image)} "
                    f"chosen_side: {choice_str} "
                    f"result: SUCCESS "
                )

                if self.video_recorder:
                    self.video_recorder(animal, True)
                self.set_success_state(1)
                animal.add_trial(True)
                if self.expe_data_saver:
                    self.expe_data_saver(True, False)

            # incorrect answer
            # ----------------
            if str(correct_image.get_opposite()) in event.description:
                logging.info(
                    f"[trial_result] room: {str(self)} "
                    f"rfid: {animal} "
                    f"attribution: {str(animal.correct_image)} "
                    f"phase: {str(animal.phase)} "
                    f"solution: {str(correct_image)} "
                    f"chosen_side: {choice_str} "
                    f"result: FAIL "
                )

                if self.video_recorder:
                    self.video_recorder(animal, False)
                self.set_fail_state(10)
                animal.add_trial(False)
                if self.expe_data_saver:
                    self.expe_data_saver(True, False)

        # Unused touches
        # ----------------
        if "missed" in event.description:
            # data: xf, yf
            if event.data is not None:
                touch_x = event.data[0]
                touch_y = event.data[1]
                logging.info(
                    f"[useless_touch] room: {str(self)} "
                    f"rfid: {animal} "
                    f"touch_x: {touch_x} "
                    f"touch_y: {touch_y} "
                )

    def waterpump_listener(self, event: DeviceEvent):
        """Function called by the waterpump when it fires an event."""
        logging.debug(f"[waterpump_event] event: {event.description} ")

        animal = self.animal_in
        if animal is None:
            self.log_animal_in_error("waterpump_listener")
            return

        if "reward picked" in event.description:
            animal.add_reward_search(True)
            logging.info(
                f"[reward_search] room: {str(self)} "
                f"rfid: {animal} "
                f"find: reward"
            )
            self.set_trial_state()

        if "animal in" in event.description:
            animal.add_reward_search(False)
            logging.info(
                f"[reward_search] room: {str(self)} "
                f"rfid: {animal} "
                f"find: nothing"
            )

    def get_all_devices(self) -> list[Any]:
        """Get all devices of the room in a list."""
        return [self.gate, self.ts, self.wp]

    def set_animal_weight(self, weight: int):
        """Set the animal weight for the gate parameters."""
        self.gate.mouseAverageWeight = weight
        logging.info(
            "[gate_expected_weight] "
            f"device: {self.gate.name} "
            f"expected_weight_set_to_(g): {weight}"
        )

    def shutdown_room(self):
        """Shutdown all hardware of the room."""
        self.gate.shutdown()
        self.ts.shutdown()
        self.wp.shutdown()

    def reset(self):
        """Reset room parameters and re-init hardware."""
        self.animal_in = None
        self.ts.enabled = False
        self.wp.rewardPicked = False
        self.wp.rewardDelivered = False
        self.init_room()

    def start_timer(
        self, duration_sec: int, callback: Callable, *args, **kwargs
    ):
        """Start a timer that will call the specified callback after the given
        duration (*in seconds*)."""
        self.running_timers.append(
            Timer(duration_sec, callback, *args, **kwargs)
        )
        self.running_timers[-1].start()

    def cancel_all_timers(self):
        """Cancel all running timers."""
        for timer in self.running_timers:
            timer.cancel()
        self.running_timers = []

    def ts_display(self, left_img: TSImage, right_img: TSImage):
        """Displays images on left and right side."""
        self.ts.clear()

        logging.info(
            "[touchscreen_display] "
            f"room: {str(self)} "
            f"left: {str(left_img)} "
            f"right: {str(right_img)} "
            f"id_left: {left_img.value} "
            f"id_right: {right_img.value} "
        )
        self.ts.setXYImage(
            f"left_image_{str(left_img)}",
            left_img.value,
            0.25,
            0.5,
            unit="ratio",
        )
        self.ts.setXYImage(
            f"right_image_{str(right_img)}",
            right_img.value,
            0.75,
            0.5,
            unit="ratio",
        )

    def ts_random_display(self, img: TSImage):
        """
        Display the image and its opposite on the touchscreen, but choose their
        sides randomly."""
        random_display = [img, img.get_opposite()]
        shuffle(random_display)

        logging.info(
            f"[touchscreen_random_display] "
            f"room: {str(self)} "
            f"image: {str(img)} "
            f"opposite: {str(img.get_opposite())} "
        )

        self.ts_display(
            left_img=random_display[0], right_img=random_display[1]
        )

    def simulate_ts_event(self, result: bool = False):
        """Trigger a random touchscreen event."""
        if result:
            img_name = str(TSImage.LIGHT)
        else:
            img_name = str(TSImage.DARK)

        self.ts.fireEvent(
            DeviceEvent(
                deviceType="touchscreen",
                deviceObject=self,
                description="symbol xy touched " + f"left_image_{img_name}",
                data=("simulate", 0, 0, 0, 0, 0),
            )
        )

        logging.info(
            "[touch_simulation] "
            f"room: {str(self)} "
            f"img_touch: {img_name} "
        )

    def clear_state(self, flush_duration: int = 0):
        """Clear the actual state of the room, in order to prepare the
        next one.
        - disable actions
        - turn off waterpump light
        - turn off touchscreen
        - flush any reward if needed (flush_duration > 0) and log it
        """
        logging.debug(f"[room_state] room: {str(self)} state: CLEAR")
        self.ts.enabled = False
        self.wp.lightOff()
        self.ts.clear()
        if flush_duration > 0:
            self.wp.flush(255, flush_duration)
            logging.info(
                "[reward_flushing] "
                f"room: {str(self)} "
                f"flush_duration_(ms): {flush_duration}"
            )

    def set_initial_state(self, animal: Animal):
        """Set room in INITIAL state. Called by *gate_listener* when an animal
        enters the room."""
        self.cancel_all_timers()

        self.animal_in = animal
        logging.info(
            "[animal_in] "
            f"room: {str(self)} "
            f"rfid: {self.animal_in.rfid} "
            f"phase: {str(self.animal_in.phase)} "
            f"attribution: {str(self.animal_in.correct_image)} "
        )
        self.clear_state()

        self.state = "INITIAL"
        logging.info(f"[room_state] room: {str(self)} state: {self.state}")
        self.set_trial_state()

    def set_exit_state(self):
        """Set room in EXIT state. Called by *gate_listener* when an animal
        exits the room."""
        self.cancel_all_timers()
        self.clear_state(500)

        self.state = "EXIT"
        logging.info(f"[room_state] room: {str(self)} state: {self.state}")

        animal = self.animal_in
        if animal is None:
            self.log_animal_in_error("set_exit_state")
        else:
            logging.info(
                "[animal_progression] "
                f"rfid: {animal} "
                f"{' '.join(animal.progression_display)}"
            )
            if animal.phase_completed():
                previous_phase = animal.phase
                animal.proceed_to_next_phase()
                logging.info(
                    "[phase_completion] "
                    f"rfid: {animal} "
                    f"completed_phase: {previous_phase} "
                    f"current_phase: {animal.phase}"
                )
            logging.info(f"[animal_out] room: {str(self)} rfid: {animal.rfid}")
        if self.expe_data_saver:
            self.expe_data_saver(True, True)
        self.animal_in = None
        self.init_room(display_log=False)  # unplugged management

    def set_success_state(self, reward_size: int):
        """Set room in SUCCESS state."""
        self.cancel_all_timers()
        self.clear_state()

        self.state = "SUCCESS"
        logging.info(f"[room_state] room: {str(self)} state: {self.state}")

        self.wp.deliverDrop(reward_size)
        self.wp.lightOn(30)
        logging.info(
            "[reward_delivery] "
            f"room: {str(self)} "
            f"reward_size: {reward_size}"
        )
        self.ts.enabled = True

    def set_fail_state(self, wait_time: int):
        """Set room in FAIL state."""
        self.cancel_all_timers()
        self.clear_state(1000)

        self.state = "FAIL"
        logging.info(f"[room_state] room: {str(self)} state: {self.state}")

        self.start_timer(wait_time, self.set_trial_state)
        self.ts.enabled = True

    def set_trial_state(self):
        """Grab the phase of animal. Update room depending on animal phase
        (basically the state where the mouse have a trial set up).
        """
        if self.expe_data_saver:
            self.expe_data_saver(True, False)

        animal = self.animal_in
        if animal is None:
            self.log_animal_in_error("set_trial_state")
            return

        self.clear_state()

        self.state = "TRIAL"
        logging.info(f"[room_state] room: {str(self)} state: {self.state}")

        self.ts_random_display(animal.get_correct_image())
        self.ts.enabled = True


class VisualDiscriminationExperiment:
    """Class that handle the whole touchscreen experiment."""

    def __init__(
        self,
        images_to_attribute: list[TSImage],
        sensors: RoomSensorDigest | None = None,
        camera_recorder: CameraRecorder | None = None,
    ):
        """Initialise the touchscreen experiment, with all hardware and
        parameters setup.

        Parameters
        ----------
        images_to_attribute : list of TSImage
            The images to assign to the animals. If auto_random_attribution
            is True (prompted at experiment start), images are assigned
            randomly with equal distribution: the list is shuffled and
            assigned to new animals in order, then reshuffled once the
            end of the list is reached.
        """

        # ================ EXPERIMENT PARAMETERS ================

        # Input images
        # ----------------
        self.images_to_attribute = images_to_attribute
        """List of images that must be attributed to the animals."""

        # Room devices
        # ----------------
        for room in Room.ALL:
            room.expe_data_saver = self.save_animals_data
            room.set_gate_listener(self.gate_listener)
            if camera_recorder:
                room.video_recorder = self.record_video

        # Global devices
        # ----------------
        self.cam_recorder = camera_recorder
        self.sensors = sensors

        # ================ EXPERIMENT ================

        # experiment settings
        # ----------------
        self.info = ExperimentSettings()
        self.info.start_experiment()
        current_date = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")
        current_exp = self.info.name + "-"
        current_exp += current_date
        os.makedirs(current_exp)
        os.chdir(current_exp)

        # logs setup
        # ----------------
        log_file = current_exp + ".log.txt"
        print("Logfile: ", log_file)
        logging.basicConfig(
            level=logging.INFO,
            filename=log_file,
            format="%(asctime)s.%(msecs)03d: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            force=True,
        )  # log message in appropriate file with time and date

        # log also in console
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

        # animals
        # ----------------
        self.animals: dict[str, Animal] = {}
        """{RFID: Animal} Dictionary with RFID as key and Animal object as
        value for all animals that entered the experiment."""
        self.animals_saver = ParameterSaver(
            Path(__file__).parent, self.info.name
        )

        # load animals data if exist, and fill self.animals with it
        for data in self.animals_saver.getData().values():
            animal = Animal.load_from_dict(data)
            self.animals[animal.rfid] = animal
            logging.info(
                f"[animal_loading] "
                f"rfid: {animal.rfid} "
                f"phase: {animal.phase} "
                f"ts_image: {animal.correct_image} "
            )
            logging.info(
                "[animal_progression] "
                f"rfid: {animal.rfid} "
                f"progression: {' '.join(animal.progression_display)}"
            )

        self.init_experiment()

        logging.info("application started")
        logging.info(f"NAME: {self.info.name}")
        logging.info(f"DATE: {current_date}")
        logging.info(f"COMMENT: {self.info.comment}")

        logging.info(
            f"[all_rooms] {' '.join([room.name for room in Room.ALL])} "
        )

    # ================ EXPERIMENT MANAGEMENT ================

    def init_experiment(self):
        """Initialise all systems."""
        for room in Room.ALL:
            room.init_room()

        if (
            self.sensors is not None
            and self.room_sensor_listener
            not in self.sensors.deviceListenerList
        ):
            self.sensors.addDeviceListener(self.room_sensor_listener)
            logging.info(
                "[init_sensors] "
                f"device: {type(self.sensors).__name__} "
                f"COM_PORT: {self.sensors.comPort} "
            )

    def shutdown_experiment(self):
        """Shutdown all systems."""
        for room in Room.ALL:
            room.shutdown_room()

        if self.cam_recorder is not None:
            self.cam_recorder.shutdown()
        if self.sensors is not None:
            self.sensors.shutdown()

        WaitForAllThreads()

    def record_video(self, animal: Animal, result: bool | None):
        """Save small video record of the trial.

        Parameters
        ----------
        trial_result : bool | None
            The result of the trial. It will be written on the video.
            If None, indicates that there is no good answer for this trial.
        """
        if self.cam_recorder is None:
            logging.info(
                "[warning] [video_recording] " "camera_recorder: NOT_SET "
            )
            return

        if result is None:
            txt = "Trial without answer"
            specific_color = (255, 0, 0)
        else:
            if result:
                txt = "Successful trial"
                specific_color = (0, 0, 255)
            else:
                txt = "Failed trial"
                specific_color = (0, 255, 0)

        txt_settings = {"fontScale": 0.5, "centered": False}
        text_list = []

        text_list.append(CRText(txt, x=10, y=10, centerX=True, **txt_settings))

        txt = f"RFID {animal.rfid}"
        text_list.append(CRText(txt, x=10, y=300, **txt_settings))

        txt = f"correct image: {str(animal.correct_image)}"
        text_list.append(CRText(txt, x=10, y=340, **txt_settings))

        txt = f"current phase: {str(animal.phase)}"
        text_list.append(CRText(txt, x=10, y=380, **txt_settings))

        text_list.append(
            CRText(
                "X",
                x=0,
                y=0,
                bgColor=specific_color,
                color=specific_color,
                **txt_settings,
            )
        )

        self.cam_recorder.delayedSave(
            delayS=5,
            minDateTime=datetime.now() - timedelta(seconds=5),
            textList=text_list,
        )

        logging.info("[video_recording] " f"video_text: {txt} ")

    def get_all_rfid(self):
        """Get all registered RFID in *animals* dictionary."""
        return list(self.animals.keys())

    def save_animals_data(
        self,
        detailed_log: bool = True,
        log_progression: bool = False,
    ):
        """Save all animals data."""
        data = {}

        if not detailed_log:
            logging.info(
                f"[animal_saving] all_rfid: {' '.join(self.animals.keys())} "
            )

        for rfid, animal in self.animals.items():
            data[rfid] = animal.save_as_dict()
            if detailed_log:
                logging.info(
                    f"[animal_saving] "
                    f"rfid: {rfid} "
                    f"phase: {animal.phase} "
                    f"ts_image: {animal.correct_image} "
                )
            if log_progression:
                logging.info(
                    "[animal_progression] "
                    f"rfid: {rfid} "
                    f"progression: {' '.join(animal.progression_display)}"
                )

        self.animals_saver.setData(data)
        self.animals_saver.save()

    def register_RFID(self, rfid: str | None):
        """Registered RFID if not already in animals."""
        if rfid is None:
            logging.info(f"[warning] [rfid_registration] rfid: {rfid}")
            return None

        all_rfid = self.get_all_rfid()

        if rfid not in all_rfid:
            self.animals[rfid] = Animal(rfid)
            logging.info(
                "[rfid_registration] "
                f"rfid: {rfid} "
                f"phase: {str(self.animals[rfid].phase)} "
            )

            if self.info.auto_random_attribution:
                img_idx = len(all_rfid) % len(self.images_to_attribute)
                if img_idx == 0:
                    shuffle(self.images_to_attribute)
                choosen_image = self.images_to_attribute[img_idx]
                self.animals[rfid].correct_image = choosen_image
            else:
                self.animals[rfid].correct_image = TSImage.ERROR

            logging.info(
                "[ts_image_attribution] "
                f"rfid: {rfid} "
                f"ts_image: {str(self.animals[rfid].correct_image)} "
            )

        return rfid

    # ================ VISUAL APP INTERACTIONS ================

    def get_ts_image(self, rfid: str):
        """Get the TSImage of the corresponding animal."""
        if rfid in self.animals.keys():
            return self.animals[rfid].correct_image
        else:
            return None

    def set_ts_image(self, rfid: str, ts_image: TSImage):
        """Set the TSImage of the corresponding animal."""
        if rfid in self.animals.keys():
            self.animals[rfid].correct_image = ts_image
            logging.info(
                "[ts_image_attribution] "
                f"rfid: {rfid} "
                f"ts_image: {str(ts_image)} "
            )

    def get_phase(self, rfid: str) -> Phase | None:
        """Get the phase of corresponding animal."""
        if rfid in self.animals.keys():
            return self.animals[rfid].phase
        else:
            return None

    def set_phase(self, rfid: str, phase: Phase):
        if rfid in self.animals.keys():
            self.animals[rfid].phase = phase
            logging.info(
                "[phase_attribution] " f"rfid: {rfid} " f"phase: {str(phase)} "
            )

    def get_all_rooms(self) -> list[Room]:
        """Get all rooms of the experiment in a list."""
        return Room.ALL

    def get_room(
        self,
        name: str | None = None,
        rfid_in: str | None = None,
    ) -> Room | None:
        """Get the room from its name (or the name of one of its devices) or
        from the rfid currently in the room."""
        if name is not None:
            return Room.get_from_name(name)

        if rfid_in is not None:
            return Room.get_from_rfid_in(rfid_in)

        return None

    # ================ LISTENERS ================

    def room_sensor_listener(self, event: DeviceEvent):
        """Function called when room sensors fire an event."""
        logging.info(event.description)

    def gate_listener(self, event: DeviceEvent):
        """Function called by the gates when they fire an event."""
        logging.debug(f"[gate_event] event: {event.description} ")
        # get room and device corresponding to event
        device_name = event.deviceObject.name  # type: ignore
        room = self.get_room(name=device_name)

        if room is None:
            return

        room_side = "UNKNOWN"
        if room.gate.order == GateOrder.ONLY_ONE_ANIMAL_IN_B:
            room_side = "B"
        if room.gate.order == GateOrder.ONLY_ONE_ANIMAL_IN_A:
            room_side = "A"

        if room_side == "A":
            home_side = "B"
        elif room_side == "B":
            home_side = "A"
        else:
            home_side = "UNKNOWN"

        # Animal weight
        # ----------------
        if "WEIGHT OK" in event.description:
            weight = float(event.description.split(" ")[-1])
            logging.info(
                "[animal_weight] "
                f"room: {str(room)} "
                f"rfid: {room.animal_in} "
                f"weight_(g): {weight} "
            )

        # Animal in
        # ----------------
        if "allowed to cross" in event.description:
            if f"TO SIDE {room_side}" in event.description:
                read_rfid = self.register_RFID(event.data)
                if read_rfid is not None:
                    room.set_initial_state(self.animals[read_rfid])
                return

        # get animal corresponding to RFID in room, if exist
        if room.animal_in is None:
            logging.debug(
                "[warning] "
                "[gate_listener] "
                f"room: {str(room)} "
                f"rfid: NOT_FOUND "
            )
            return

        # Animal out
        # ----------------
        if f"FREE TO GET TO SIDE {home_side}" in event.description:
            room.set_exit_state()
            return

        # Animal info
        # ----------------
        # reading time ?
        # animal weight ?
