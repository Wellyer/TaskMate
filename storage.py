"""
storage.py - Saves and loads TaskMate data in a local JSON file.

The file looks like this:
    {
        "version": 1,
        "tasks": [ {"id": 1, "title": "...", ...}, ... ]
    }

Saving is done safely: data is first written to a temporary file and then
moved over the real file, so a crash in the middle of saving cannot wipe
out the existing data.
"""

import json
import os
import tempfile
from datetime import datetime

from task_manager import Task

DATA_FILE_NAME = "tasks.json"
DATA_FILE_VERSION = 1


def get_default_data_path():
    """Return the path of tasks.json, stored in the same folder as the program."""
    folder = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(folder, DATA_FILE_NAME)


def _backup_corrupted_file(file_path):
    """Rename a damaged data file so the user does not lose it.

    Returns the new file name, or None if the rename was not possible.
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    root, extension = os.path.splitext(file_path)
    backup_path = f"{root}.corrupt-{timestamp}{extension}"
    try:
        os.replace(file_path, backup_path)
        return backup_path
    except OSError:
        return None


def load_tasks(file_path=None):
    """Read the tasks from the JSON file.

    Returns a tuple (tasks, warning_message).
    - tasks is a list of Task objects (empty if there is no usable data).
    - warning_message is None when everything loaded cleanly, otherwise a
      text message that the GUI can show to the user.
    The function never raises an exception for missing or broken files.
    """
    file_path = file_path or get_default_data_path()

    # First run: no file yet, so start with an empty list
    if not os.path.exists(file_path):
        return [], None

    try:
        with open(file_path, "r", encoding="utf-8") as data_file:
            content = data_file.read()
    except OSError as error:
        return [], f"Could not open the data file ({error}). Starting with an empty list."

    # An empty file is treated as "no tasks yet"
    if not content.strip():
        return [], None

    try:
        raw_data = json.loads(content)
    except json.JSONDecodeError as error:
        backup = _backup_corrupted_file(file_path)
        return [], _corruption_message("The data file is not valid JSON", error, backup)

    # Accept the normal {"tasks": [...]} format, or a plain list
    if isinstance(raw_data, dict):
        task_entries = raw_data.get("tasks")
    elif isinstance(raw_data, list):
        task_entries = raw_data
    else:
        task_entries = None

    if not isinstance(task_entries, list):
        backup = _backup_corrupted_file(file_path)
        return [], _corruption_message("The data file has an unexpected structure", None, backup)

    tasks = []
    skipped_count = 0
    for entry in task_entries:
        try:
            tasks.append(Task.from_dict(entry))
        except (ValueError, TypeError, KeyError):
            # Skip only the broken entry; keep the rest of the tasks
            skipped_count += 1

    warning = None
    if skipped_count:
        warning = f"{skipped_count} saved task(s) were invalid and could not be loaded."
    return tasks, warning


def _corruption_message(problem, error, backup):
    """Build the warning text shown when the data file is damaged."""
    message = f"{problem}"
    if error is not None:
        message += f" ({error})"
    message += ". TaskMate started with an empty task list."
    if backup:
        message += f"\n\nThe damaged file was saved as:\n{backup}"
    return message


def save_tasks(tasks, file_path=None):
    """Write all tasks to the JSON file.

    Raises OSError if the file cannot be written (the GUI shows this to the user).
    """
    file_path = file_path or get_default_data_path()
    folder = os.path.dirname(os.path.abspath(file_path))
    data = {
        "version": DATA_FILE_VERSION,
        "tasks": [task.to_dict() for task in tasks],
    }

    # Write to a temporary file first, then replace the real file in one step
    temp_fd, temp_path = tempfile.mkstemp(dir=folder, prefix="tasks-", suffix=".tmp")
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as temp_file:
            json.dump(data, temp_file, indent=4, ensure_ascii=False)
            temp_file.write("\n")
        os.replace(temp_path, file_path)
    except BaseException:
        # Clean up the temporary file if something went wrong
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise
