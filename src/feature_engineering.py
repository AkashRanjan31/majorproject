"""
feature_engineering.py
----------------------
Create keyboard and mouse behavior features from the raw TSV log files.

The raw dataset stores events such as key presses, mouse movement, clicks, and
fatigue labels. For every fatigue label timestamp, this file looks back over the
previous 30 minutes and calculates simple, understandable features.
"""

from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "dataset" / "Data"
DATASET_CSV = PROJECT_ROOT / "dataset" / "dataset.csv"
USERS = ["user 1", "user 2"]
WINDOW_SECS = 30 * 60

FEATURE_COLUMNS = [
    "key_press_count",
    "key_hold_time",
    "typing_speed",
    "error_rate",
    "backspace_count",
    "idle_time",
    "mouse_click_count",
    "left_click",
    "right_click",
    "double_click",
    "scroll_count",
    "cursor_speed",
    "cursor_distance",
    "drag_count",
    "movement_speed",
    "idle_mouse_time",
]

FATIGUE_MAP = {
    "Above_Avg": 0,
    "V_High": 0,
    "No": 0,       # "No" fatigue = Normal
    "Avg": 1,
    "Below_Avg": 2,
    "Low": 2,
}


def parse_times(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Convert timestamp columns to datetime values."""
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce")
    return df


def get_window(df: pd.DataFrame, time_col: str, end_time: pd.Timestamp) -> pd.DataFrame:
    """Return rows from the 30 minutes before the fatigue label timestamp."""
    start_time = end_time - pd.Timedelta(seconds=WINDOW_SECS)
    mask = (df[time_col] >= start_time) & (df[time_col] <= end_time)
    return df.loc[mask].copy()


def keyboard_features(keystrokes: pd.DataFrame, inactivity: pd.DataFrame, end_time: pd.Timestamp) -> dict:
    """Calculate keyboard behavior features for one 30-minute window."""
    window = get_window(keystrokes, "Press_Time", end_time)
    key_press_count = len(window)

    if key_press_count > 0:
        hold_time = (window["Relase_Time"] - window["Press_Time"]).dt.total_seconds()
        key_hold_time = hold_time.clip(0, 2).mean()
    else:
        key_hold_time = 0.0

    character_count = len(window[window["Key"] == "$"])
    typing_speed = (character_count / 5) / (WINDOW_SECS / 60)

    backspace_count = len(window[window["Key"].astype(str).str.lower() == "backspace"])
    error_rate = backspace_count / key_press_count if key_press_count else 0.0

    keyboard_idle = inactivity[inactivity["Type"].astype(str).str.lower() == "keyboard"]
    keyboard_idle_window = get_window(keyboard_idle, "Stopped_Time", end_time)
    idle_time = keyboard_idle_window["Duration(s)"].sum() if not keyboard_idle_window.empty else 0.0

    return {
        "key_press_count": key_press_count,
        "key_hold_time": round(float(key_hold_time), 4),
        "typing_speed": round(float(typing_speed), 2),
        "error_rate": round(float(error_rate), 4),
        "backspace_count": backspace_count,
        "idle_time": round(float(idle_time), 2),
    }


def mouse_features(mouse_data: pd.DataFrame, inactivity: pd.DataFrame, end_time: pd.Timestamp) -> dict:
    """Calculate mouse behavior features for one 30-minute window."""
    window = get_window(mouse_data, "Time", end_time)

    left_click = len(window[window["Event_Type"] == "Left_Pressed"])
    right_click = len(window[window["Event_Type"] == "Right_Pressed"])
    mouse_click_count = left_click + right_click

    left_clicks = window[window["Event_Type"] == "Left_Pressed"].sort_values("Time")
    if len(left_clicks) > 1:
        click_gaps = left_clicks["Time"].diff().dt.total_seconds().dropna()
        double_click = int((click_gaps < 0.3).sum())
    else:
        double_click = 0

    scroll_count = len(window[window["Event_Type"] == "Scroll"])

    moves = window[window["Event_Type"] == "Move"].sort_values("Time")
    cursor_distance = 0.0
    cursor_speed = 0.0
    movement_speed = 0.0
    if len(moves) > 1:
        dx = moves["X"].diff().fillna(0)
        dy = moves["Y"].diff().fillna(0)
        distances = np.sqrt(dx**2 + dy**2)
        cursor_distance = float(distances.sum())

        active_seconds = (moves["Time"].iloc[-1] - moves["Time"].iloc[0]).total_seconds()
        if active_seconds > 0:
            cursor_speed = cursor_distance / active_seconds
            movement_speed = cursor_speed

    drag_count = count_drags(window)

    mouse_idle = inactivity[inactivity["Type"].astype(str).str.lower() == "mouse"]
    mouse_idle_window = get_window(mouse_idle, "Stopped_Time", end_time)
    idle_mouse_time = mouse_idle_window["Duration(s)"].sum() if not mouse_idle_window.empty else 0.0

    return {
        "mouse_click_count": mouse_click_count,
        "left_click": left_click,
        "right_click": right_click,
        "double_click": double_click,
        "scroll_count": scroll_count,
        "cursor_speed": round(float(cursor_speed), 2),
        "cursor_distance": round(float(cursor_distance), 1),
        "drag_count": drag_count,
        "movement_speed": round(float(movement_speed), 2),
        "idle_mouse_time": round(float(idle_mouse_time), 2),
    }


def count_drags(mouse_window: pd.DataFrame) -> int:
    """Count simple drag actions: left press, move, then left release."""
    events = mouse_window[
        mouse_window["Event_Type"].isin(["Left_Pressed", "Move", "Left_Released"])
    ].sort_values("Time")

    drag_count = 0
    is_pressed = False
    moved_after_press = False

    for _, row in events.iterrows():
        event = row["Event_Type"]
        if event == "Left_Pressed":
            is_pressed = True
            moved_after_press = False
        elif event == "Move" and is_pressed:
            moved_after_press = True
        elif event == "Left_Released" and is_pressed:
            if moved_after_press:
                drag_count += 1
            is_pressed = False
            moved_after_press = False

    return drag_count


def map_fatigue(raw_value: str) -> int:
    """Map the raw fatigue value to 0=Normal, 1=Moderate, 2=High Fatigue."""
    return FATIGUE_MAP.get(str(raw_value).strip(), 1)


def build_feature_dataset(save_csv: bool = True) -> pd.DataFrame:
    """Build the complete feature table from all available users."""
    all_rows = []

    for user in USERS:
        user_path = DATA_ROOT / user
        if not user_path.exists():
            continue

        keystrokes = pd.read_csv(user_path / "keystrokes.tsv", sep="\t")
        mouse_data = pd.read_csv(user_path / "mousedata.tsv", sep="\t")
        user_condition = pd.read_csv(user_path / "usercondition.tsv", sep="\t")
        inactivity = pd.read_csv(user_path / "inactivity.tsv", sep="\t")

        for frame in [keystrokes, mouse_data, user_condition, inactivity]:
            frame.drop(columns=[c for c in frame.columns if c.startswith("Unnamed")], inplace=True)

        keystrokes = parse_times(keystrokes, ["Press_Time", "Relase_Time"])
        mouse_data = parse_times(mouse_data, ["Time"])
        user_condition = parse_times(user_condition, ["Time"])
        inactivity = parse_times(inactivity, ["Stopped_Time", "Activated_Time"])

        print(f"Processing {user}: {len(user_condition)} label rows")

        for _, label_row in user_condition.iterrows():
            end_time = label_row["Time"]
            if pd.isnull(end_time):
                continue

            row = {}
            row.update(keyboard_features(keystrokes, inactivity, end_time))
            row.update(mouse_features(mouse_data, inactivity, end_time))
            row["fatigue_level"] = map_fatigue(label_row["Fatigue_Val"])
            all_rows.append(row)

    dataset = pd.DataFrame(all_rows)
    dataset = dataset[FEATURE_COLUMNS + ["fatigue_level"]]

    if save_csv:
        DATASET_CSV.parent.mkdir(parents=True, exist_ok=True)
        dataset.to_csv(DATASET_CSV, index=False)
        print(f"Saved engineered dataset to {DATASET_CSV}")

    print(f"Total samples: {len(dataset)}")
    print("Class distribution:")
    print(dataset["fatigue_level"].value_counts().sort_index().to_string())
    return dataset


if __name__ == "__main__":
    df = build_feature_dataset()
    print(df.head())
