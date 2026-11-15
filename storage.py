"""
storage.py - Saves and loads TaskMate data in local JSON files.

tasks.json looks like this:
    {
        "version": 1,
        "tasks": [ {"id": 1, "title": "...", ...}, ... ]
    }

settings.json stores the chosen interface language, e.g. {"language": "ar"}.

Saving is done safely: data is first written to a temporary file and then
moved over the real file, so a crash in the middle of saving cannot wipe
out the existing data.
"""

import json
import os
import shutil
import tempfile
from collections import namedtuple
from datetime import datetime

from i18n import DEFAULT_LANGUAGE, LANGUAGES
from task_manager import Task

DATA_FILE_NAME = "tasks.json"
SETTINGS_FILE_NAME = "settings.json"
DATA_FILE_VERSION = 1

# A message for the user, stored as a translation key plus its parameters.
# The GUI turns it into text with i18n.t(notice.key, **notice.params).
Notice = namedtuple("Notice", ["key", "params"])


def _project_file(file_name):
    """Return the path of a file stored in the same folder as the program."""
    folder = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(folder, file_name)


def get_default_data_path():
    """Return the path of tasks.json."""
    return _project_file(DATA_FILE_NAME)


def get_settings_path():
    """Return the path of settings.json."""
    return _project_file(SETTINGS_FILE_NAME)


def _timestamp():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _backup_name(file_path, label):
    """Build a backup name such as tasks.corrupt-20261115-101500.json."""
    root, extension = os.path.splitext(file_path)
    return f"{root}.{label}-{_timestamp()}{extension}"


def _move_corrupted_file(file_path):
    """Rename a damaged data file so the user does not lose it.

    Returns the new path, or None if the rename was not possible.
    """
    backup_path = _backup_name(file_path, "corrupt")
    try:
        os.replace(file_path, backup_path)
        return backup_path
    except OSError:
        return None


def _copy_original_file(file_path):
    """Keep a copy of a file that has some invalid entries. Returns the copy path or None."""
    backup_path = _backup_name(file_path, "invalid-backup")
    try:
        shutil.copy2(file_path, backup_path)
        return backup_path
    except OSError:
        return None


def load_tasks(file_path=None):
    """Read the tasks from the JSON file.

    Returns a tuple (tasks, notice).
    - tasks is a list of Task objects (empty if there is no usable data).
    - notice is None when everything loaded cleanly, otherwise a Notice
      that the GUI can show to the user.
    The function never raises an exception for missing or broken files.
    """
    file_path = file_path or get_default_data_path()

    # First run: no file yet, so start with an empty list
    if not os.path.exists(file_path):
        return [], None

    try:
        with open(file_path, "r", encoding="utf-8") as data_file:
            content = data_file.read()
    except (OSError, UnicodeDecodeError) as error:
        return [], Notice("warn_open_failed", {"error": error})

    # An empty file is treated as "no tasks yet"
    if not content.strip():
        return [], None

    try:
        raw_data = json.loads(content)
    except json.JSONDecodeError as error:
        return [], _damaged_file_notice(file_path, "warn_invalid_json", {"error": error})

    # Accept the normal {"tasks": [...]} format, or a plain list
    if isinstance(raw_data, dict):
        task_entries = raw_data.get("tasks")
    elif isinstance(raw_data, list):
        task_entries = raw_data
    else:
        task_entries = None

    if not isinstance(task_entries, list):
        return [], _damaged_file_notice(file_path, "warn_bad_structure", {})

    tasks = []
    skipped_count = 0
    for entry in task_entries:
        try:
            tasks.append(Task.from_dict(entry))
        except (ValueError, TypeError, KeyError):
            # Skip only the broken entry; keep the rest of the tasks
            skipped_count += 1

    notice = None
    if skipped_count:
        # The next save rewrites the file without the invalid entries,
        # so keep a copy of the original first.
        copy_path = _copy_original_file(file_path) or file_path
        notice = Notice("warn_skipped_tasks", {"count": skipped_count, "path": copy_path})
    return tasks, notice


def _damaged_file_notice(file_path, key, params):
    """Move the damaged file aside and build the message that explains it."""
    backup = _move_corrupted_file(file_path)
    params = dict(params)
    params["backup_path"] = backup  # None if the file could not be moved
    return Notice(key, params)


def save_tasks(tasks, file_path=None):
    """Write all tasks to the JSON file.

    Raises OSError if the file cannot be written (the GUI shows this to the user).
    """
    file_path = file_path or get_default_data_path()
    data = {
        "version": DATA_FILE_VERSION,
        "tasks": [task.to_dict() for task in tasks],
    }
    _write_json_atomically(data, file_path)


def load_language(file_path=None):
    """Return the saved interface language, or the default if none is saved."""
    file_path = file_path or get_settings_path()
    try:
        with open(file_path, "r", encoding="utf-8") as settings_file:
            language = json.load(settings_file).get("language")
    except (OSError, ValueError, AttributeError):
        return DEFAULT_LANGUAGE
    return language if language in LANGUAGES else DEFAULT_LANGUAGE


def save_language(language, file_path=None):
    """Remember the interface language. Raises OSError if it cannot be written."""
    file_path = file_path or get_settings_path()
    _write_json_atomically({"language": language}, file_path)


def _write_json_atomically(data, file_path):
    """Write data as JSON using a temporary file, then replace the real file."""
    folder = os.path.dirname(os.path.abspath(file_path))
    temp_fd, temp_path = tempfile.mkstemp(dir=folder, prefix="tmp-", suffix=".tmp")
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
