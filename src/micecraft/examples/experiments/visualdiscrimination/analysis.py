import os
import sys
import logging
from pathlib import Path
from typing import Any, Callable, Literal
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from tqdm import tqdm
import plotly.express as px
import plotly.graph_objects as go
from plotly.colors import sequential, qualitative

from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QFormLayout,
    QDialogButtonBox,
    QVBoxLayout,
)

from micecraft.soft.report.LogFileMerger import LogFileMerger
from micecraft.examples.report.report_manager import HTMLReportManager

DISCRETE_CLRS = qualitative.Bold[::-1]
CONTINUOUS_CLRS = sequential.Plotly3


class LogLineParser:
    """Class for parsing one line of log and extracting relevant data."""

    @staticmethod
    def separate_room_device(device_name: str) -> tuple[str, str]:
        """Separate the room name and the device name from a string of format
        'room-device'. Also remove any brackets ("[", "]") around the input
        device name.

        Returns:
            (room, device): A tuple containing the room name and the device
            name.
        """
        device_name = device_name.strip("[]")
        split = device_name.split("-")
        room = split[0]
        device = split[1]
        return room, device

    def __init__(self, log_line: str):
        self.log_line = log_line
        self.log_split = self.get_log().split(" ")
        self.tag, self.warning = self.get_tag()

    def get_tag(self) -> tuple[str, bool]:
        """Extract the tags of the log line."""
        tag = self.log_split[0]
        warning = False
        if tag == "[warning]":
            warning = True
            tag = self.log_split[1]

        return tag, warning

    def get_time(self) -> datetime:
        """Extract the time of the log line as a datetime format."""
        time = datetime.strptime(self.log_line[0:23], "%Y-%m-%d %H:%M:%S.%f")
        return time

    def get_log(self) -> str:
        """Extract the log message from the log line. Begin after the ': ' that
        follows the timestamp."""
        return self.log_line[25:-1]

    def get_info(self, name: str) -> str | None:
        """Extract the information from the log line."""
        if not name.endswith(":"):
            name += ":"
        for i, s in enumerate(self.log_split):
            if s == name:
                return self.log_split[i + 1]
        return None

    def get_room(self) -> str:
        """Extract the room name from the log line."""
        room_name = self.get_info("room")
        if room_name is None:
            room_device = self.get_info("room-device")
            if room_device is None:
                raise ValueError(
                    f"Room name not found in log line:\n {self.log_line}"
                )
            room_name, _ = self.separate_room_device(room_device)
        return room_name

    def get_sensors_data(self) -> dict[str, datetime | float]:
        """Extract relevant data from one line of log."""
        data: dict[str, datetime | float] = {}
        list_str = self.get_log().strip("}{").split(", ")
        values = []
        # mean Pressure, std Pressure, max Pressure, min Pressure
        # mean Temperature, std Temperature, max Temperature, min Temperature
        # mean Humidity, std Humidity, max Humidity, min Humidity
        # mean r, std r, max r, min r
        # mean g, std g, max g, min g
        # mean b, std b, max b, min b
        # mean a, std a, max a, min a
        # mean Sound level, std Sound level, max Sound level, min Sound level
        # mean Tilting x, std Tilting x, max Tilting x, min Tilting
        # mean Tilting y, std Tilting y, max Tilting y, min Tilting y
        # mean Shock, std Shock, max Shock, min Shock
        # mean Raw accel x, std Raw accel x, max Raw accel x, min Raw accel x
        # mean Raw accel y, std Raw accel y, max Raw accel y, min Raw accel y
        # mean Raw accel z, std Raw accel z, max Raw accel z, min Raw accel z
        for s in list_str:
            [_, value] = s.split(": ")
            values.append(float(value))
        data["time"] = self.get_time()
        data["pressure"] = values[0]
        data["pressure_std"] = values[1]
        data["temperature"] = values[4]
        data["temperature_std"] = values[5]
        data["humidity"] = values[8]
        data["humidity_std"] = values[9]
        data["light"] = values[24]
        data["light_std"] = values[25]
        data["sound"] = values[28]
        data["sound_std"] = values[29]

        return data


class TrialData:

    def __init__(self, session_id: int, room: str) -> None:

        self.current_state: str = "UNKNOWN"
        """Current state of the room."""

        self.session_id = session_id
        """The session ID for the trial. Indepedent from the animal."""
        self.room = room
        """The room where the trial took place."""
        self.left_display: str | None = None
        """The image displayed on the left side of the touchscreen."""
        self.right_display: str | None = None
        """The image displayed on the right side of the touchscreen."""
        self.solution_image: str | None = None
        """The image corresponding to the correct answer for the trial."""
        self.touch_left: bool | None = None
        """The side touched by the animal for the trial answer.
        None if no touch."""
        self.trial_result: bool | None = None
        """Result of the trial (True if correct, False if incorrect)."""
        self.x_touch: float | None = None
        """X position of the answer (touch). Other touches coordinates are not
        stored."""
        self.y_touch: float | None = None
        """Y position of the answer (touch). Other touches coordinates are not
        stored."""
        self.reward_collected: bool | None = None
        """Animal got the reward."""

        self.state_start: dict[str, datetime] = {}
        """States start time."""
        self.state_end: dict[str, datetime] = {}
        """States end time."""
        self.state_searches: dict[str, int] = {}
        """Number of searches during a state (went inside water pump)."""
        self.state_touches: dict[str, int] = {}
        """Number of touches during a state."""

    def as_dict(self) -> dict:
        """Return as dict for DataFrame export."""
        state_duration: dict[str, timedelta | None] = {}
        trial_start = datetime.max
        for state in self.state_start.keys():
            start = self.state_start[state]
            if start < trial_start:
                trial_start = start
            end = self.state_end[state]
            if start and end:
                state_duration[state] = end - start
            else:
                state_duration[state] = None

        return {
            "session_id": self.session_id,
            "room": self.room,
            "trial_time": trial_start,
            "left_display": self.left_display,
            "right_display": self.right_display,
            "solution_image": self.solution_image,
            "touch_left": self.touch_left,
            "trial_result": self.trial_result,
            "x_touch": self.x_touch,
            "y_touch": self.y_touch,
            "reward_collected": self.reward_collected,
            **{f"{k}_state_duration": v for k, v in state_duration.items()},
            **{
                f"{k}_state_searches": v
                for k, v in self.state_searches.items()
            },
            **{f"{k}_state_touches": v for k, v in self.state_touches.items()},
        }


class SessionData:

    _id_counter: int = 0

    def __init__(self, room_name: str) -> None:
        self.session_id = SessionData._id_counter
        """The session ID for the trial. Indepedent from the animal."""
        SessionData._id_counter += 1

        self.room: str = room_name
        """Name of the room where the session took place."""
        self.rfid_reading_failure: int = 0
        """Number of failed RFID readings before this session."""
        self.rfid_read_in: int | None = None
        """Number of attempted RFID readings before this session."""
        self.phase: str | None = None
        """Current phase of the animal for this session."""
        self.rfid: str | None = None
        """RFID number of the animal in the session."""
        self.start_time: datetime | None = None
        """Session start time."""
        self.end_time: datetime | None = None
        """Session end time."""
        self.weight_in: float | None = None
        """Animal weight measured in the gate when beginning session."""
        self.weight_out: float | None = None
        """Animal weight measured in the gate when ending session."""

    def as_dict(self) -> dict:
        """Return as dict for DataFrame export."""

        return {
            "session_id": self.session_id,
            "rfid": self.rfid,
            "room": self.room,
            "phase": self.phase,
            "weight_in": self.weight_in,
            "weight_out": self.weight_out,
            "rfid_read_in": self.rfid_read_in,
            "rfid_reading_failure": self.rfid_reading_failure,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }


class AnimalData:
    def __init__(self, rfid: str) -> None:
        self.rfid: str = rfid
        """RFID number of the animal."""
        self.ts_image: str | None = None
        """Attributed touch screen image."""


class LogAnalyzer(object):

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.sensors: list[dict[str, Any]] = []
        self.sessions: list[SessionData] = []
        self.trials: list[TrialData] = []

        self.animals: list[AnimalData] = []
        """List of animals' data (RFID and attributed touch screen image)."""

        self.zero = self.get_zero()

    def get_zero(self):
        with open(self.log_file) as f:
            line = f.readline()
            parser = LogLineParser(line)
            time_zero = parser.get_time()
        return time_zero

    def to_csv(self) -> tuple[Path, Path, Path]:
        """Export the extracted data to csv files and return their paths as
        *(sensors, sessions, trials)*."""
        folder_path = self.log_file.parent
        file_name = str(self.log_file).strip(".txt").strip(".log")

        sensors_df = pd.DataFrame(self.sensors)
        sensors_csv_path = folder_path / f"{file_name}.sensors.csv"
        sensors_df.to_csv(sensors_csv_path, index=False)

        sessions_df = pd.DataFrame([s.as_dict() for s in self.sessions])
        sessions_csv_path = folder_path / f"{file_name}.sessions.csv"
        sessions_df.to_csv(sessions_csv_path, index=False)

        trials_df = pd.DataFrame([t.as_dict() for t in self.trials])
        trials_csv_path = folder_path / f"{file_name}.trials.csv"
        trials_df.to_csv(trials_csv_path, index=False)

        return sensors_csv_path, sessions_csv_path, trials_csv_path

    def process_log(self):
        """Process each line of log file and extract data."""

        with open(self.log_file) as f:

            # (room_name: Data)
            # keep track of sessions and trials in all rooms at the same time
            trial: dict[str, TrialData] = {}
            session: dict[str, SessionData] = {}

            lines = f.readlines()
            for line in tqdm(lines, desc="Parsing log files"):

                # sort out irrelevant data
                # ----------------
                # (relevant line always start at least with the year, so "2")
                if line[0] != "2":
                    continue

                # initialise parser
                # ----------------
                parser = LogLineParser(line)

                if parser.warning:
                    continue

                # Rooms initialisation
                # ----------------
                if parser.tag == "[all_rooms]" and not session:
                    # r
                    rooms_name = parser.log_split[1:]
                    session = {name: SessionData(name) for name in rooms_name}
                    trial = {
                        name: TrialData(session[name].session_id, name)
                        for name in rooms_name
                    }
                    continue

                # Animal registration
                # ----------------
                if parser.tag == "[rfid_registration]":
                    # rfid: 000000000000 phase: 00-BLACK_WHITE
                    rfid = parser.get_info("rfid")
                    assert rfid is not None, f"{parser.tag} bug"
                    self.animals.append(AnimalData(rfid))
                    continue

                if parser.tag == "[ts_image_attribution]":
                    # rfid: 000000000000 ts_image: FLOWER
                    rfid = parser.get_info("rfid")
                    assert rfid is not None, f"{parser.tag} bug"
                    for animal in self.animals:
                        if animal.rfid == rfid:
                            animal.ts_image = parser.get_info("ts_image")
                    continue

                # Sensors
                # ----------------
                if parser.get_log().startswith("{'mean Pressure':"):
                    self.sensors.append(parser.get_sensors_data())
                    continue

                # Animal weight
                # ----------------
                if "[animal_weight]" in parser.get_log():
                    # room: r-d rfid: 000000000000 weight_(g): 23.00
                    room = parser.get_room()
                    weight = parser.get_info("weight_(g)")
                    if weight is None:
                        tqdm.write(
                            "Animal weight reading error in log:\n"
                            f"{parser.log_line}"
                        )
                    else:
                        weight = float(weight)

                    if session[room].rfid is None:
                        session[room].weight_in = weight
                    else:
                        session[room].weight_out = weight
                    continue

                # RFID reading
                # ----------------
                if "[RFID CHECK]" == parser.get_log()[0:12]:
                    # [RFID CHECK][rA-Gate] RFID 000000000000 read in: 3 / 100 time: 0.33 seconds side: TO SIDE B
                    room_device = parser.get_log()[13:].split(" ")[0]
                    room, _ = parser.separate_room_device(room_device)

                    if session[room].rfid is not None:
                        tqdm.write(
                            "RFID read while in session in log:\n "
                            f"{parser.log_line}"
                        )

                    if "read in:" in parser.get_log():
                        nb_read_in = parser.get_info("in")
                        if nb_read_in is not None:
                            session[room].rfid_read_in = int(nb_read_in)

                    if "Can't read ID" in parser.get_log():
                        session[room].rfid_reading_failure += 1
                    continue

                # Session end
                # ----------------
                # END session if application restarted or if animal exit room

                if parser.get_log() == "application started":
                    for room in session.keys():
                        if session[room].rfid is not None:
                            tqdm.write("Application restarted during session.")

                            if (
                                trial[room].current_state
                                in trial[room].state_start
                            ):
                                trial[room].state_end[
                                    trial[room].current_state
                                ] = parser.get_time()
                            session[room].end_time = parser.get_time()
                            self.sessions.append(session[room])
                            session[room] = SessionData(room)
                        if (
                            room in trial
                            and trial[room].current_state != "UNKNOWN"
                        ):
                            tqdm.write("Application restarted during trial.")
                            self.trials.append(trial.pop(room))
                    continue

                if parser.tag == "[animal_out]":
                    # room: r animal: 000000000000
                    room = parser.get_room()

                    if session[room].rfid is None:
                        continue
                    else:
                        session[room].end_time = parser.get_time()
                        self.sessions.append(session[room])
                        session[room] = SessionData(room)
                    continue

                # Session start
                # ----------------
                if parser.tag == "[animal_in]":
                    # room: r animal: 000000000000
                    room = parser.get_room()

                    if session[room].rfid is not None:
                        tqdm.write(
                            "Animal entered while in session in log:\n "
                            f"{parser.log_line}"
                        )
                        self.sessions.append(session[room])
                        session[room] = SessionData(room)

                    session[room].rfid = parser.get_info("rfid")
                    session[room].phase = parser.get_info("phase")
                    session[room].start_time = parser.get_time()
                    continue

                # State
                # ----------------
                if parser.tag == "[room_state]":
                    # room: r state: TRIAL
                    room = parser.get_room()

                    if session[room].rfid is None:
                        continue

                    state = parser.get_info("state")
                    if state is None:
                        tqdm.write(
                            "Unknown state in log:\n " f"{parser.log_line}"
                        )
                        continue

                    if room not in trial:
                        if state in ["INITIAL"]:
                            trial[room] = TrialData(
                                session[room].session_id,
                                room,
                            )
                            trial[room].current_state = state
                            trial[room].state_start[state] = parser.get_time()
                            continue

                    if trial[room].current_state in trial[room].state_start:
                        trial[room].state_end[
                            trial[room].current_state
                        ] = parser.get_time()

                    if state == "EXIT":
                        self.trials.append(trial.pop(room))
                        continue

                    if state == "TRIAL":
                        if trial[room].current_state != "INITIAL":
                            self.trials.append(trial.pop(room))
                            trial[room] = TrialData(
                                session[room].session_id,
                                room,
                            )

                    if state not in ["CLEAR", "EXIT"]:
                        trial[room].current_state = state
                        trial[room].state_start[state] = parser.get_time()
                    continue

                # Touch screen display
                # ----------------
                if parser.tag == "[touchscreen_display]":
                    # room-device: r-TS left: PLANE right: FLOWER id_left: 0 id_right: 1
                    room = parser.get_room()
                    trial[room].left_display = parser.get_info("left")
                    trial[room].right_display = parser.get_info("right")

                # Touches
                # ----------------
                if parser.tag == "[useful_touch]":
                    # room: r rfid: 000000000000 image_name: left_image_FLOWER image_id: 1 image_x: 560.0 image_y: 750.0 touch_x_px: 100 touch_y_px: 300 touch_x_ratio: 0.250 touch_y_ratio: 0.500
                    room = parser.get_room()
                    x = parser.get_info("touch_x_ratio")
                    y = parser.get_info("touch_y_ratio")
                    if x is None and y is None:
                        x = parser.get_info("touch_x_px")
                        y = parser.get_info("touch_y_px")
                    if x is None and y is None:
                        x = parser.get_info("touch_x")
                        y = parser.get_info("touch_y")

                    if x is not None:
                        trial[room].x_touch = float(x)
                    if y is not None:
                        trial[room].y_touch = float(y)
                    continue

                if parser.tag == "[useless_touch]":
                    # room: r rfid: 000000000000 touch_x_px: 100 touch_y_px: 300 touch_x_ratio: 0.250 touch_y_ratio: 0.500
                    room = parser.get_room()
                    if (
                        trial[room].state_touches.get(
                            trial[room].current_state
                        )
                        is None
                    ):
                        trial[room].state_touches[
                            trial[room].current_state
                        ] = 1
                    else:
                        trial[room].state_touches[
                            trial[room].current_state
                        ] += 1
                    continue

                # Trial result
                # ----------------
                if parser.tag == "[trial_result]":
                    # room: r rfid: 000000000000 attribution: FLOWER phase: 00-BLACK_WHITE solution: LIGHT chosen_side: left result: FAIL
                    room = parser.get_room()
                    trial[room].solution_image = parser.get_info("solution")

                    result = parser.get_info("result")
                    if result == "SUCCESS":
                        trial[room].trial_result = True
                    elif result == "FAIL":
                        trial[room].trial_result = False

                    side = parser.get_info("chosen_side")
                    if side == "left":
                        trial[room].touch_left = True
                    elif side == "right":
                        trial[room].touch_left = False
                    continue

                # Reward searches
                # ----------------
                if parser.tag == "[reward_search]":
                    # room: r rfid: 000000000000
                    room = parser.get_room()

                    state = trial[room].current_state
                    if state not in trial[room].state_searches:
                        trial[room].state_searches[state] = 1
                    else:
                        trial[room].state_searches[state] += 1

                # Reward picking
                # ----------------
                if parser.tag == "[reward_delivery]":
                    # room: r reward_size: 1
                    room = parser.get_room()
                    trial[room].reward_collected = False

                # Reward picking
                # ----------------
                if parser.tag == "[reward_picked]":
                    # room: r rfid: 000000000000
                    room = parser.get_room()
                    trial[room].reward_collected = True


def select_files(file_type: str) -> list[Path]:
    """Open a dialog to select at least one file of the specified type."""
    file_type = file_type.strip(".").lower()
    while True:
        files, _ = QFileDialog.getOpenFileNames(
            None,
            f"Select {file_type.upper()} files",
            str(Path.home()),
            f"{file_type.upper()} files (*.{file_type});;All files (*)",
        )
        if not files:
            sys.exit(0)

        files_list = [Path(f) for f in files if f.endswith(f".{file_type}")]
        if files_list:
            return files_list

        QMessageBox.warning(
            None,
            f"No {file_type.upper()} files found",
            (
                f"The selected files do not contain any .{file_type} file.\n"
                f"Please select valid {file_type.upper()} files."
            ),
        )


def merge_logs(log_files: list[Path]) -> Path:
    """Merge the selected log files and return the path for log analysis."""

    if len(log_files) == 1:
        return log_files[0]

    merged_path = log_files[0].parent / "merged"
    merged_path.mkdir(exist_ok=True)

    print("Start merging...")
    merger = LogFileMerger(log_files, str(merged_path) + os.sep)
    print("Logs merged.")

    return Path(merger.mergedFiles[0])


def get_cumulative(
    df: pd.DataFrame,
    on_col: str,
    fill_na: bool | int | float | None = None,
    map_arg: dict | Callable | None = None,
    groupby_col: str | None = "rfid",
) -> pd.Series:
    """Compute cumulative sum of a column (per RFID by default),
    optionally mapping values and filling NAs.

    Returns
    -------
    pandas.Series
        A series containing the cumulative sum (per RFID).
    """
    series = df[on_col]
    if map_arg is not None:
        series = series.map(map_arg)
    if fill_na is not None:
        series = series.fillna(fill_na).astype(type(fill_na))
    if groupby_col is not None:
        series = series.groupby(df[groupby_col], observed=True)
    return series.cumsum()


def get_streak(
    df: pd.DataFrame,
    col_name: str,
    counted_value: Any,
    groupby_col: str | None = "rfid",
):
    """
    Count consecutive streaks of a given value per RFID.

    Parameters
    ----------
    col_name : str
        Name of the pandas series containing the values to check for
        streaks.
    counted_value : any, default=True
        The value to count streaks of. Consecutive occurrences of this
        value are accumulated until a different value appears.

    Returns
    -------
    pandas.Series
        A pandas series where each entry represents the current streak
        length of `counted_value` for the corresponding RFID.

    Notes
    -----
    - Streaks are computed separately for each RFID in `df_rfid`.
    - When `df_values[i] != counted_value`, the streak counter for that RFID is reset to 0.
    - Multiple RFIDs are tracked in parallel.
    """
    if groupby_col is not None:
        groupby_idx = {k: v for v, k in enumerate(df[groupby_col].unique())}
        streaks = [0 for _ in groupby_idx]
    else:
        groupby_idx = {0: 0}
        streaks = [0]
    out = []

    for i, v in enumerate(df[col_name]):
        if groupby_col is not None:
            group_value = df[groupby_col].iloc[i]
        else:
            group_value = 0

        if v == counted_value:
            streaks[groupby_idx[group_value]] += 1
        else:
            streaks[groupby_idx[group_value]] = 0

        out.append(streaks[groupby_idx[group_value]])

    return pd.Series(out, index=df[col_name].index)


def get_accuracy(
    df: pd.DataFrame,
    on_col: str,
    window: int,
    groupby_col: str = "rfid",
):
    """
    Compute rolling mean (accuracy) of the last `window` non-null values of
    `value_col` per RFID. Returns a pandas Series aligned with df.index.
    The result is continuous series (one value per row).
    """

    def _rolling(group):
        result = []
        for idx in group.index:
            vals = group.loc[:idx, on_col]
            vals = vals[vals.notnull()]
            if len(vals) >= window:
                mean_val = vals.iloc[-window:].mean()
            else:
                mean_val = np.nan
            result.append(mean_val)
        return pd.Series(result, index=group.index, name="new_col")

    series = df.groupby(groupby_col, group_keys=False, observed=True).apply(
        _rolling
    )
    return series


def plot_two_columns(df, x_col, y_cols, color_col, line_dash_map=None):
    """
    Plot 2 columns of a dataframe as lines with different dash styles.

    Parameters
    ----------
    df : pd.DataFrame
        The dataframe containing the data.
    x_col : str
        Column name for x-axis.
    y_cols : list[str]
        Two column names to plot as y values.
    color_col : str
        Column name to determine colors.
    line_dash_map : dict, optional
        Mapping of y_cols to dash styles, e.g. {"col1": "solid", "col2": "dash"}.
        If None, defaults to first solid, second dashed.

    Returns
    -------
    fig : plotly.graph_objs.Figure
    """

    if len(y_cols) != 2:
        raise ValueError("y_cols must contain exactly 2 column names.")

    # Default dash map
    if line_dash_map is None:
        line_dash_map = {y_cols[0]: "solid", y_cols[1]: "dash"}

    df_long = df.melt(
        id_vars=[x_col, color_col],
        value_vars=y_cols,
        var_name="variable",
        value_name="value",
    )

    line_dash_sequence = [line_dash_map[y_col] for y_col in y_cols]

    fig = px.line(
        df_long,
        x=x_col,
        y="value",
        color=color_col,
        color_discrete_sequence=DISCRETE_CLRS,
        line_dash="variable",
        line_dash_sequence=line_dash_sequence,
    )

    return fig


def day_or_night(time, night_begin: int, night_duration: int):
    hour = time.hour
    night_hours = np.arange(night_begin, night_begin + night_duration) % 24
    return "night" if hour in night_hours else "day"


class AnalysisOptionDialog(QDialog):
    """Dialog asking the user which analysis option to run."""

    LOGS = 0
    RAW_CSV = 1
    PROCESSED_CSV = 2

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Analysis options")
        self.choice: int | None = None

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel("From which step do you want to start your analysis?")
        )

        for label, value in [
            ("Log(s) file(s)", self.LOGS),
            ("Original CSV file", self.RAW_CSV),
            ("Computed CSV file", self.PROCESSED_CSV),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, v=value: self._select(v))
            layout.addWidget(btn)

    def _select(self, value: int) -> None:
        self.choice = value
        self.accept()


class NightParametersDialog(QDialog):
    """Ask user for night parameters: begin hour and duration (hours)."""

    def __init__(
        self, parent=None, default_begin: int = 20, default_duration: int = 12
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Night parameters")

        self.night_begin_spin = QSpinBox(self)
        self.night_begin_spin.setRange(0, 23)
        self.night_begin_spin.setValue(default_begin)

        self.night_duration_spin = QSpinBox(self)
        self.night_duration_spin.setRange(0, 24)
        self.night_duration_spin.setValue(default_duration)

        form = QFormLayout()
        form.addRow("Night begin (hour 0-23)", self.night_begin_spin)
        form.addRow("Night duration (hours)", self.night_duration_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def get_values(self) -> tuple[int, int]:
        return int(self.night_begin_spin.value()), int(
            self.night_duration_spin.value()
        )


def draw_nights(
    fig: go.Figure,
    start_time: pd.Timestamp,
    end_time: pd.Timestamp,
    night_begin: int | None,
    night_duration: int,
):
    """Draw night periods on a plotly figure as shaded areas."""
    if night_begin is None:
        return fig
    time = start_time
    while time < end_time:
        if time.hour == night_begin:
            x0 = time
            x1 = time + pd.Timedelta(hours=night_duration)
            if x1 > end_time:
                x1 = end_time
            fig.add_vrect(
                x0=x0,
                x1=x1,
                line_width=0,
                fillcolor="black",
                layer="below",
                opacity=0.1,
            )
        time += pd.Timedelta(hours=1)
    return fig


def plt_curve_std(
    df,
    x_col,
    y_col,
    y_col_std,
    x_lbl=None,
    y_lbl=None,
    title=None,
    name=None,
):
    """Generate a plotly figure with a curve and its standard deviation as a
    shaded area."""

    std_up = df[y_col] + df[y_col_std]
    std_low = df[y_col] - df[y_col_std]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=list(df[x_col]) + list(df[x_col])[::-1],
            y=list(std_up) + list(std_low)[::-1],
            fill="toself",
            fillcolor="rgba(255, 151, 255, 0.2)",
            line=dict(color="rgba(255,255,255,0)"),  # no border
            hoverinfo="skip",
            showlegend=True,
            name="± std",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df[x_col],
            y=df[y_col],
            mode="lines",
            name=name,
            line=dict(color="rgba(255, 151, 255, 1.0)"),
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title=x_col if x_lbl is None else x_lbl,
        yaxis_title=y_col if y_lbl is None else y_lbl,
    )

    return fig


def draw_phases(
    fig: go.Figure,
    sessions: pd.DataFrame,
    x_col: str,
    orientation: Literal["v", "h"] = "v",
):
    """Draw vertical or horizontal lines on a plotly figure to indicate the
    start of each phase for each RFID.
    """
    rfids = sessions["rfid"].unique()
    phases = sessions["phase"].unique()
    for rfid in rfids:
        for phase in phases:
            line_x = sessions[
                (sessions["phase"] == phase) & (sessions["rfid"] == rfid)
            ][x_col].min()
            if line_x is pd.NaT:
                continue
            if orientation == "v":
                fig.add_vline(
                    x=line_x,
                    layer="below",
                    line_width=1,
                    line_dash="dot",
                    line_color=DISCRETE_CLRS[
                        list(rfids).index(rfid) % len(DISCRETE_CLRS)
                    ],
                )
            if orientation == "h":
                fig.add_hline(
                    y=line_x,
                    layer="below",
                    line_width=1,
                    line_dash="dot",
                    line_color=DISCRETE_CLRS[
                        list(rfids).index(rfid) % len(DISCRETE_CLRS)
                    ],
                )
    return fig


def get_hour_overlap_ratio(t_begin, t_end):
    """
    Calculate the percentage of each hour overlapped by a given time interval.

    Parameters
    ----------
    t_begin : pd.Timestamp
        Start timestamp of the interval
    t_end : pd.Timestamp
        End timestamp of the interval

    Returns
    -------
    pd.DataFrame
        DataFrame with `time`, `hour`, `day`, and `hour_ratio` of each
        hour covered by the interval
    """
    hours = pd.date_range(t_begin.floor("h"), t_end.floor("h"), freq="h")
    results = []
    for t in hours:
        h_start = t
        h_end = t + pd.Timedelta(hours=1)
        overlap_start = max(t_begin, h_start)
        overlap_end = min(t_end, h_end)
        if overlap_end > overlap_start:
            duration = (overlap_end - overlap_start).total_seconds()
            results.append(
                {
                    "time": t,
                    "date": t.date(),
                    "hour": t.hour,
                    "day": t.day,
                    "hour_ratio": duration / 3600,
                }
            )
    return pd.DataFrame(results)


def insert_trials_report(
    report_manager: HTMLReportManager,
    tdf: pd.DataFrame,
    sdf: pd.DataFrame,
    night_begin: int,
    night_duration: int,
):

    pbar = tqdm(total=14, desc="Generating trials reports", unit="report")

    trial_content = """
    <div style="width:80%; margin: 0 auto; text-align: center;">
        <div style="margin-bottom:1em;">
            A <i>trial</i> is define between two <i>trial state</i> or between one 
            <i>initial state</i> and a <i>trial state</i>. It begin either when an
            animal enter the test or when the <i>trial state</i> is set, and ends
            when the next <i>trial state</i> is set. It often correpond to the
            animal is proposed a test with image displayed to the moment it collect
            the reward. A <i>session</i> (see <i>id_session</i>) is define between
            two gate moment : the moment the animal is allowed into the test zone
            and the moment it is free to go in the house. During a <i>session</i>,
            there is a least one trial, but multiple can occur.
            All times and durations are in seconds (s).
        </div>
    </div>
    """
    report_manager.add_title("Mice trials datas", content=trial_content)

    # =======================================
    title = "Phases timeline"
    # =======================================
    df_plot = sdf.groupby(
        ["rfid", "phase"], as_index=False, observed=True
    ).agg({"start_time": "min", "end_time": "max"})

    fig1 = px.timeline(
        df_plot,
        x_start="start_time",
        x_end="end_time",
        y="rfid",
        color="phase",
        color_discrete_sequence=sequential.Electric_r,
    )
    fig1.update_layout(
        xaxis_title="Time",
        yaxis_title="RFID",
        legend_title="Phases",
        showlegend=False,
    )

    df_plot = tdf.groupby(
        ["rfid", "phase"], as_index=False, observed=True, sort=False
    )["cumul_trials_total"].max()

    df_plot["phase_trials"] = (
        df_plot.groupby("rfid", as_index=False, observed=True)[
            "cumul_trials_total"
        ]
        .diff()
        .fillna(df_plot["cumul_trials_total"])
    )

    fig2 = px.bar(
        df_plot,
        x="phase_trials",
        y="rfid",
        color="phase",
        color_discrete_sequence=sequential.Electric_r,
        orientation="h",
    )
    fig2.update_layout(
        xaxis_title="Trials",
        yaxis_title="RFID",
        legend_title="Phases",
        showlegend=False,
    )

    explanations = """
    Overview of the time (left) and number of trials (right) took by each 
    mouse (RFID) for each phases.
    """
    report_manager.add_multi_fig_report(
        title,
        [fig1, fig2],
        top_note=explanations,
    )

    report_manager.add_title("Mice accuracy")

    pbar.update(1)
    # =======================================
    title = "Accuracy over last 50 trials"
    # =======================================
    fig = px.line(
        tdf,
        "cumul_trials_total",
        "accuracy_50",
        color="rfid",
        color_discrete_sequence=DISCRETE_CLRS,
    )
    fig = draw_phases(fig, tdf, "cumul_trials_total")
    fig.update_layout(
        xaxis_title="Cumulative trials",
        yaxis_title="Accuracy over last 50 trials",
        legend_title="RFID",
        showlegend=True,
        yaxis=dict(range=[0, 1]),
    )

    explanations = """
        Accuracy over the last 50 trials for each mouse (RFID). Each point
        represents a trials, and an accuracy for each trial is calculated with
        this one and the 49 that preceded it.
        """
    report_manager.add_report(title, fig, top_note=explanations)

    pbar.update(1)
    # =======================================
    title = "Superposed accuracy per trials - reversal start"
    # =======================================

    nb_rfids = tdf["rfid"].nunique()
    fig = go.Figure()
    rfids = tdf["rfid"].unique()

    phases = tdf["phase"].unique()
    reversal = None
    for phase in phases:
        if "reversal" in phase.lower():
            reversal = phase

    for rfid_idx, rfid in enumerate(rfids):
        fig.add_trace(
            go.Scatter(
                x=tdf[tdf["rfid"] == rfid]["cumul_trials_total"]
                - tdf[(tdf["rfid"] == rfid) & (tdf["phase"] == reversal)][
                    "cumul_trials_total"
                ].min(),
                y=tdf[tdf["rfid"] == rfid][f"accuracy_50"],
                mode="lines",
                name=f"RFID {rfid}",
                line=dict(color=DISCRETE_CLRS[rfid_idx % len(DISCRETE_CLRS)]),
                opacity=0.8,
            )
        )

    fig.update_layout(
        xaxis_title="Cumulative trials",
        yaxis_title="Accuracy",
        yaxis=dict(range=[0, 1]),
        legend_title="RFID",
        showlegend=True,
    )

    explanations = """
        Overview of the accuracy for each mouse (RFID) with a choosable trials
        window, and with a synchronisation on the reversal begginning. Each
        point represents a trials, and an accuracy for each trial is calculated
        with this one and the 49 that preceded it.
        """
    report_manager.add_report(title, fig, top_note=explanations)

    pbar.update(1)
    # =======================================
    title = "Accuracy over last 50 trials (time axis)"
    # =======================================
    fig = px.line(
        tdf,
        "trial_time",
        "accuracy_50",
        color="rfid",
        color_discrete_sequence=DISCRETE_CLRS,
    )
    fig = draw_phases(fig, sdf, "start_time")
    fig.update_layout(
        xaxis_title="Trial begin time",
        yaxis_title="Accuracy over last 50 trials",
        legend_title="RFID",
        showlegend=True,
        yaxis=dict(range=[0, 1]),
    )
    fig = draw_nights(
        fig,
        tdf["trial_time"].min(),
        tdf["trial_time"].max(),
        night_begin,
        night_duration,
    )

    explanations = """
        Accuracy over the last 50 trials for each mouse (RFID). Each point
        represents a trials, and an accuracy for each trial is calculated with
        this one and the 49 that preceded it. The x axis is time instead of
        trials count.
        """
    report_manager.add_report(title, fig, top_note=explanations)

    pbar.update(1)
    # =======================================
    title = "Trials per hour of the day"
    # =======================================
    df_plot = (
        tdf.groupby(["rfid", "hour"], observed=True)
        .size()
        .reset_index(name="count")
        .sort_values(by="hour")
    )
    df_plot["hour"] = df_plot["hour"].astype(str) + "h"

    fig1 = px.bar_polar(
        df_plot,
        r="count",
        theta="hour",
        color="rfid",
        color_discrete_sequence=DISCRETE_CLRS,
    )

    fig1.update_layout(
        polar=dict(radialaxis=dict(title=dict(text="Trial count"))),
        legend_title="RFID",
    )

    fig2 = px.line_polar(
        df_plot,
        r="count",
        theta="hour",
        line_close=True,
        color="rfid",
        color_discrete_sequence=DISCRETE_CLRS,
    )

    fig2.update_layout(
        polar=dict(radialaxis=dict(title=dict(text="Trial count"))),
        legend_title="RFID",
    )

    explanations = """
        Number of trials performed by each mouse (RFID) for each hour of the
        day. The graphs on left and right are the same data displayed in
        different ways: histogram on left and line on right.
        """
    report_manager.add_multi_fig_report(
        title,
        [fig1, fig2],
        top_note=explanations,
    )

    pbar.update(1)
    # =======================================
    title = "Test zone occupancy"
    # =======================================

    results = []
    for (session, rfid), group in sdf.groupby(
        ["session_id", "rfid"], observed=True
    ):
        t_begin = group["start_time"].min()
        t_end = group["end_time"].max()
        if t_begin == t_end:
            continue
        hourly = get_hour_overlap_ratio(t_begin, t_end)
        hourly["hour_percent"] = hourly["hour_ratio"] * 100
        hourly["rfid"] = str(rfid)
        hourly["id_session"] = str(session)
        results.append(hourly)
    df_plot = pd.concat(results, ignore_index=True)

    fig = px.bar(
        df_plot,
        x="time",
        y="hour_percent",
        color="rfid",
        color_discrete_sequence=DISCRETE_CLRS,
    )

    fig = draw_nights(
        fig,
        sdf["start_time"].min(),
        sdf["start_time"].max(),
        night_begin,
        night_duration,
    )

    fig.update_layout(
        xaxis_title="Hours of the day",
        yaxis_title="Occupancy time (%)",
        legend_title="RFID",
        showlegend=True,
        yaxis=dict(range=[0, 100]),
    )

    explanations = """
        Percentage of time spent in the test zone for each hour of the day and
        by each mouse (RFID).
        """
    report_manager.add_report(title, fig, top_note=explanations)

    pbar.update(1)
    # =======================================
    title = "Cumulative reward delivered and taken"
    # =======================================
    fig = plot_two_columns(
        tdf,
        x_col="trial_time",
        y_cols=["cumul_reward_collected", "cumul_reward_delivered"],
        color_col="rfid",
    )
    fig.update_layout(
        xaxis_title="Trial begin time",
        yaxis_title="Cumulative reward",
        legend_title="RFID",
        showlegend=True,
    )
    fig = draw_phases(fig, tdf, "trial_time")
    fig = draw_nights(
        fig,
        tdf["trial_time"].min(),
        tdf["trial_time"].max(),
        night_begin,
        night_duration,
    )

    explanations = """
        Overview of the cumulative reward delivered and taken for each mouse
        (RFID). A reward taken has been collected by the mouse, while a reward
        delivered has been given by the system (but not necessarily collected).
        The difference between these two curves indicates the reward loss."
        """
    report_manager.add_report(title, fig, top_note=explanations)

    pbar.update(1)
    # =======================================
    title = "Cumulative reward loss"
    # =======================================
    fig = px.line(
        tdf,
        "trial_time",
        "cumul_reward_lossed",
        color="rfid",
        color_discrete_sequence=DISCRETE_CLRS,
    )
    fig = draw_phases(fig, tdf, "trial_time")
    fig = draw_nights(
        fig,
        tdf["trial_time"].min(),
        tdf["trial_time"].max(),
        night_begin,
        night_duration,
    )

    fig.update_layout(
        xaxis_title="Trial begin time",
        yaxis_title="Cumulative reward loss",
        legend_title="RFID",
        showlegend=True,
    )

    explanations = """
        Overview of the rewards lost by each mouse (RFID). When a horizontal
        line is observed, it means the mouse has understood the delivery system
        and is collecting all the rewards it can."
        """
    report_manager.add_report(title, fig, top_note=explanations)

    pbar.update(1)
    # =======================================
    title = "Cumulative left or right touch (-1 for left, +1 for right)"
    # =======================================
    xmax = abs(tdf["cumul_choice"]).max()

    fig = px.line(
        tdf,
        "cumul_choice",
        "cumul_trials_total",
        color="rfid",
        color_discrete_sequence=DISCRETE_CLRS,
    )
    fig = draw_phases(fig, tdf, "cumul_trials_total", orientation="h")
    fig.update_layout(
        xaxis_title="Cumulative touch choice (-1 for left, +1 for right)",
        yaxis_title="Trials",
        legend_title="RFID",
        showlegend=True,
        xaxis=dict(range=[-xmax, xmax]),
    )

    explanations = """
        Overview of the cumulative left or right touch choices for each mouse
        (RFID). A value of -1 indicates a left touch, while +1 indicates a
        right touch. A left (right) trend indicates a majority of left (right)
        touches. A vertical trend indicates an equal number of left and
        right touches.
        """
    report_manager.add_report(title, fig, top_note=explanations)

    pbar.update(1)
    # =======================================
    title = "Attempts for RFID reading"
    # =======================================
    fig = px.scatter(
        sdf,
        "start_time",
        "rfid_read_in",
        marginal_x="histogram",
        marginal_y="histogram",
        facet_col="rfid",
        color="rfid",
        color_discrete_sequence=DISCRETE_CLRS,
    )
    # fig = draw_nights(
    #     fig,
    #     sdf["start_time"].min(),
    #     sdf["start_time"].max(),
    #     night_begin,
    #     night_duration,
    # )
    for ann in fig.layout.annotations:
        ann.text = ""  # remove titles from facets
    fig.update_xaxes(title_text=None)  # remove x axis labels from facets
    fig.update_layout(
        yaxis_title="RFID reading attemps",
        legend_title="RFID",
        showlegend=True,
    )

    explanations = """
        When a mouse (RFID) is in the gate (detected by its weight), the system
        tries to read its RFID tag. This plot shows the number of attempts made
        before successfully reading the RFID tag. It cannot goes beyond 100. If
        100 is reached, it is count as a "miss read". The total miss reads are
        showed in the experiment summary.
        """
    report_manager.add_report(title, fig, top_note=explanations)

    pbar.update(1)
    # =======================================
    title = "XY touch positions"
    # =======================================
    fig = px.density_heatmap(
        tdf,
        x="x_touch",
        y="y_touch_corrected",
        marginal_x="violin",
        marginal_y="violin",
        color_continuous_scale=CONTINUOUS_CLRS,
        nbinsx=32,
        nbinsy=32,
        facet_col="rfid",
        facet_col_wrap=2,
    )
    fig.update_layout(
        xaxis_title="X position (px)",
        yaxis_title="Y position (px)",
        showlegend=True,
    )

    explanations = """
        Density heatmap of where the mouse (RFID) has touch the screen for each
        of their trials.
        """
    report_manager.add_report(title, fig, top_note=explanations)

    report_manager.add_title("Mice efficiency and behavior")

    pbar.update(1)
    # =======================================
    title = "Successful touch in a row"
    # =======================================
    fig1 = px.scatter(
        tdf,
        "trial_time",
        "success_in_a_row",
        marginal_x="histogram",
        marginal_y="histogram",
        color="rfid",
        color_discrete_sequence=DISCRETE_CLRS,
    )
    fig1 = draw_nights(
        fig1,
        tdf["trial_time"].min(),
        tdf["trial_time"].max(),
        night_begin,
        night_duration,
    )
    fig1 = draw_phases(fig1, tdf, "trial_time")
    fig1.update_layout(
        yaxis_title="Successful touches in a row",
        legend_title="RFID",
    )

    fig2 = px.scatter(
        tdf,
        "cumul_trials_total",
        "success_in_a_row",
        marginal_x="histogram",
        marginal_y="histogram",
        color="rfid",
        color_discrete_sequence=DISCRETE_CLRS,
    )
    fig2 = draw_phases(fig2, tdf, "cumul_trials_total")
    fig2.update_layout(
        yaxis_title="Successful touches in a row",
        legend_title="RFID",
    )

    explanations = """
        Number of successful touches in a row for each mouse (RFID). It is
        shown against time (left) and against trials (right).
        """
    report_manager.add_multi_fig_report(
        title,
        [fig1, fig2],
        top_note=explanations,
    )

    pbar.update(1)
    # =======================================
    title = "Failed touch in a row"
    # =======================================
    fig1 = px.scatter(
        tdf,
        "trial_time",
        "fail_in_a_row",
        marginal_x="histogram",
        marginal_y="histogram",
        color="rfid",
        color_discrete_sequence=DISCRETE_CLRS,
    )
    fig1 = draw_nights(
        fig1,
        tdf["trial_time"].min(),
        tdf["trial_time"].max(),
        night_begin,
        night_duration,
    )
    fig1 = draw_phases(fig1, tdf, "trial_time")
    fig1.update_layout(
        yaxis_title="Failed touches in a row",
        legend_title="RFID",
        showlegend=True,
    )

    fig2 = px.scatter(
        tdf,
        "cumul_trials_total",
        "fail_in_a_row",
        marginal_x="histogram",
        marginal_y="histogram",
        color="rfid",
        color_discrete_sequence=DISCRETE_CLRS,
    )
    fig2 = draw_phases(fig2, tdf, "cumul_trials_total")
    fig2.update_layout(
        yaxis_title="Failed touches in a row",
        legend_title="RFID",
        showlegend=True,
    )

    explanations = """
        Number of failed touches in a row for each mouse (RFID). It is
        shown against time (left) and against trials (right).
        """
    report_manager.add_multi_fig_report(
        title,
        [fig1, fig2],
        top_note=explanations,
    )

    pbar.update(1)
    # =======================================
    title = "Time before picking reward"
    # =======================================
    fig = px.scatter(
        tdf,
        "trial_time",
        "SUCCESS_state_duration",
        color="rfid",
        marginal_x="histogram",
        marginal_y="histogram",
        color_discrete_sequence=DISCRETE_CLRS,
    )

    fig.update_layout(
        xaxis_title="Trial begin time",
        yaxis_title="Duration of SUCCESS state (s)",
        legend_title="RFID",
        showlegend=True,
    )
    fig = draw_nights(
        fig,
        tdf["trial_time"].min(),
        tdf["trial_time"].max(),
        night_begin,
        night_duration,
    )
    fig = draw_phases(fig, tdf, "trial_time")

    explanations = """
        Time, in seconds, taken by each mouse (RFID) to pick the reward after a successful
        touch.
        """
    report_manager.add_report(title, fig, top_note=explanations)

    pbar.update(1)
    # =======================================
    title = "Animal weights during experiment"
    # =======================================
    fig = px.scatter(
        sdf,
        "start_time",
        "weight_in",
        color="rfid",
        marginal_y="histogram",
        color_discrete_sequence=DISCRETE_CLRS,
    )
    fig = draw_phases(fig, sdf, "start_time")
    fig.update_layout(
        xaxis_title="Session begin time",
        yaxis_title="Weight (g)",
        legend_title="RFID",
        showlegend=True,
    )

    explanations = """
        Weight of each mouse (RFID) during the experiment. Each point
        represents the weight recorded when entering or exiting the test zone.
        """
    report_manager.add_report(title, fig, top_note=explanations)

    #######################################
    #   TABLES   #
    #######################################
    report_manager.add_table_headers(name="Trials table", df=tdf)

    report_manager.add_table_headers(name="Sessions table", df=sdf)

    return report_manager


def insert_sensors_report(
    report_manager: HTMLReportManager,
    df: pd.DataFrame,
    night_begin,
    night_duration,
):
    """Generate reports for the sensors data.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the sensors data.
    night_begin : int
        The beginning hour of the night period.
    night_duration : int
        The duration of the night period in hour.
    """

    explanations = """
        Overview of the sensors data collected during the experiment. Light and
        sound levels are not calibrated but an ampiric value is sufficient for
        a significant information.
        """
    report_manager.add_title("Sensors data", content=explanations)

    fig = plt_curve_std(
        df,
        "time",
        "temperature",
        "temperature_std",
        y_lbl="Temperature (°C)",
    )
    fig = draw_nights(
        fig,
        df["time"].min(),
        df["time"].max(),
        night_begin,
        night_duration,
    )
    report_manager.add_report("Temperature", fig)

    fig = plt_curve_std(
        df, "time", "pressure", "pressure_std", y_lbl="Pressure (kPa)"
    )
    fig = draw_nights(
        fig,
        df["time"].min(),
        df["time"].max(),
        night_begin,
        night_duration,
    )
    report_manager.add_report("Pressure", fig)

    fig = plt_curve_std(
        df, "time", "humidity", "humidity_std", y_lbl="Humidity (%)"
    )
    fig = draw_nights(
        fig,
        df["time"].min(),
        df["time"].max(),
        night_begin,
        night_duration,
    )
    report_manager.add_report("Humidity", fig)

    fig = plt_curve_std(df, "time", "light", "light_std", y_lbl="Light (?)")
    fig = draw_nights(
        fig,
        df["time"].min(),
        df["time"].max(),
        night_begin,
        night_duration,
    )
    report_manager.add_report("Light", fig)

    fig = plt_curve_std(df, "time", "sound", "sound_std", y_lbl="Sound (?)")
    fig = draw_nights(
        fig,
        df["time"].min(),
        df["time"].max(),
        night_begin,
        night_duration,
    )
    report_manager.add_report("Sound", fig)

    #######################################
    #   TABLE   #
    #######################################
    report_manager.add_table_headers(name="Sensors table", df=df)

    return report_manager


if __name__ == "__main__":

    app = QApplication(sys.argv)

    # Ask which analysis to run
    # ----------------
    dialog = AnalysisOptionDialog()
    exit = False
    if not dialog.exec():
        sys.exit(0)

    option = dialog.choice
    if option is None:
        QMessageBox.warning(
            None,
            "Bug in option selection",
            (
                "A bug occurred in the option selection dialog. "
                "Please try again or contact support."
            ),
        )
        sys.exit(0)

    if option <= AnalysisOptionDialog.LOGS:
        logging.info(
            f"Analysis option selected: {option} - One or multiple logs files"
        )

        # Load and merge logs
        # ----------------
        log_files = select_files(".log.txt")
        merged_file = merge_logs(log_files)

        # Create csv files
        # ----------------
        if merged_file is not None:
            extractor = LogAnalyzer(merged_file)
            extractor.process_log()
            sensors_path, sessions_path, trials_path = extractor.to_csv()
        else:
            QMessageBox.warning(
                None,
                "No log files selected",
                (
                    "No log files were selected for analysis. "
                    "Please select at least one log file."
                ),
            )
            sys.exit(0)

    else:
        # Load csv files
        # ----------------
        csv_files = select_files(".csv")
        sensors_path, sessions_path, trials_path = None, None, None

        for f in csv_files:
            if f.name.endswith(".sensors.csv"):
                sensors_path = f
            if f.name.endswith(".sessions.csv"):
                sessions_path = f
            if f.name.endswith(".trials.csv"):
                trials_path = f

        if (
            sensors_path is None
            or sessions_path is None
            or trials_path is None
        ):
            QMessageBox.warning(
                None,
                "Missing CSV files",
                (
                    "Please select all three CSV files (sensors, sessions and "
                    "trials) to run the analysis from CSV files."
                ),
            )
            sys.exit(0)

    # sensors_df = pd.read_csv(sensors_path, parse_dates=["time"])
    sessions_df = pd.read_csv(
        sessions_path,
        parse_dates=["start_time", "end_time"],
        dtype={"rfid": str},
    )
    trials_df = pd.read_csv(trials_path, parse_dates=["trial_time"])

    # ask user for night parameters (beginning hour and duration)
    night_dialog = NightParametersDialog()
    if not night_dialog.exec():
        night_begin, night_duration = 20, 12
    else:
        night_begin, night_duration = night_dialog.get_values()

    if option <= AnalysisOptionDialog.RAW_CSV:

        # Merge session information (rfid, phase) into the trials dataframe
        # Keep only trials that have a matching session (inner join)
        trials_df = trials_df.merge(
            sessions_df[["session_id", "rfid", "phase"]],
            on="session_id",
            how="inner",
        )

        # ================ TRIALS ================

        # cumulatives
        trials_df["cumul_reward_collected"] = get_cumulative(
            trials_df,
            on_col="reward_collected",
            fill_na=False,
        )

        trials_df["cumul_reward_delivered"] = get_cumulative(
            trials_df,
            on_col="reward_collected",
            map_arg={True: True, False: True},
            fill_na=False,
        )

        trials_df["cumul_reward_lossed"] = (
            trials_df["cumul_reward_delivered"]
            - trials_df["cumul_reward_collected"]
        )

        trials_df["cumul_choice"] = get_cumulative(
            trials_df,
            on_col="touch_left",
            map_arg={True: -1, False: 1},
            fill_na=0,
        )

        trials_df["cumul_trials_total"] = get_cumulative(
            trials_df,
            on_col="trial_result",
            map_arg={True: True, False: True},
            fill_na=False,
        )

        trials_df["cumul_trials_result"] = get_cumulative(
            trials_df,
            on_col="trial_result",
            map_arg={True: +1, False: -1},
            fill_na=False,
        )

        # streaks
        trials_df["success_in_a_row"] = get_streak(
            trials_df, col_name="trial_result", counted_value=True
        )

        trials_df["fail_in_a_row"] = get_streak(
            trials_df, col_name="trial_result", counted_value=False
        )

        # accuracy
        trials_df[f"accuracy_50"] = get_accuracy(
            trials_df, on_col="trial_result", window=50
        )

        trials_df["y_touch_corrected"] = (
            trials_df["y_touch"].max() - trials_df["y_touch"]
        )

        # others
        trials_df["hour"] = trials_df["trial_time"].dt.hour
        trials_df["day"] = trials_df["trial_time"].dt.date
        trials_df["day_or_night"] = trials_df["trial_time"].apply(
            day_or_night, args=(night_begin, night_duration)
        )

        # ================ SAVE ================
        name = trials_path.name.replace(".trials.csv", "_processed.trials.csv")
        trials_df.to_csv(trials_path.parent / name, index=False)

    report_manager = HTMLReportManager()
    report_manager.reports_creation_focus("TouchScreen Analysis")
    report_manager = insert_trials_report(
        report_manager,
        trials_df,
        sessions_df,
        night_begin,
        night_duration,
    )
    # report_manager = insert_sensors_report(
    #     report_manager,
    #     sensors_df,
    #     night_begin,
    #     night_duration,
    # )

    report_manager.generate_local_output(trials_path.parent / "Analysis")

    report_manager.open_local_output(trials_path.parent / "Analysis")
