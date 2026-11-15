"""
task_manager.py - Core task logic for TaskMate.

This module contains the Task data class, input validation, and the
TaskManager class that adds, edits, deletes, completes, filters, sorts and
summarises tasks. It does NOT use Tkinter, so it can be tested on its own.
"""

from dataclasses import dataclass
from datetime import date, datetime

# Allowed values (used by the GUI drop-down menus and by validation)
PRIORITIES = ("Low", "Medium", "High")
STATUSES = ("Pending", "Completed")
DATE_FORMAT = "%Y-%m-%d"  # Example: 2026-12-31

# Used to sort tasks: a higher number means a more important task
PRIORITY_RANK = {"Low": 1, "Medium": 2, "High": 3}

# Maximum lengths to keep the interface and JSON file tidy
MAX_TITLE_LENGTH = 100
MAX_SUBJECT_LENGTH = 60
MAX_DESCRIPTION_LENGTH = 1000


class TaskValidationError(ValueError):
    """Raised when user input or stored task data is not valid."""


def parse_due_date(text):
    """Convert 'YYYY-MM-DD' text into a date object.

    Raises TaskValidationError if the text is empty or not a real date.
    """
    cleaned = str(text).strip()
    if not cleaned:
        raise TaskValidationError("Due date is required (format YYYY-MM-DD).")
    try:
        return datetime.strptime(cleaned, DATE_FORMAT).date()
    except ValueError:
        raise TaskValidationError(
            f"'{cleaned}' is not a valid due date. Use YYYY-MM-DD, e.g. 2026-12-31."
        )


def validate_task_fields(title, description="", subject="", due_date="",
                         priority="Medium", status="Pending"):
    """Check all task fields and return a cleaned dictionary.

    Raises TaskValidationError with a user-friendly message on the first problem.
    """
    clean_title = str(title or "").strip()
    clean_description = str(description or "").strip()
    clean_subject = str(subject or "").strip()
    clean_due = str(due_date or "").strip()

    if not clean_title:
        raise TaskValidationError("The task title cannot be empty.")
    if len(clean_title) > MAX_TITLE_LENGTH:
        raise TaskValidationError(f"The title must be {MAX_TITLE_LENGTH} characters or fewer.")
    if len(clean_subject) > MAX_SUBJECT_LENGTH:
        raise TaskValidationError(f"The subject must be {MAX_SUBJECT_LENGTH} characters or fewer.")
    if len(clean_description) > MAX_DESCRIPTION_LENGTH:
        raise TaskValidationError(
            f"The description must be {MAX_DESCRIPTION_LENGTH} characters or fewer."
        )

    parse_due_date(clean_due)  # raises if the date is invalid

    if priority not in PRIORITIES:
        raise TaskValidationError("Priority must be Low, Medium or High.")
    if status not in STATUSES:
        raise TaskValidationError("Status must be Pending or Completed.")

    return {
        "title": clean_title,
        "description": clean_description,
        "subject": clean_subject,
        "due_date": clean_due,
        "priority": priority,
        "status": status,
    }


@dataclass
class Task:
    """One student task."""

    task_id: int
    title: str
    description: str
    subject: str
    due_date: str      # stored as 'YYYY-MM-DD'
    priority: str      # 'Low', 'Medium' or 'High'
    status: str        # 'Pending' or 'Completed'

    def is_completed(self):
        return self.status == "Completed"

    def due_date_value(self):
        """Return the due date as a date object."""
        return parse_due_date(self.due_date)

    def is_overdue(self, today=None):
        """A task is overdue when it is still pending and its due date has passed."""
        today = today or date.today()
        return (not self.is_completed()) and self.due_date_value() < today

    def to_dict(self):
        """Convert the task to a plain dictionary for JSON storage."""
        return {
            "id": self.task_id,
            "title": self.title,
            "description": self.description,
            "subject": self.subject,
            "due_date": self.due_date,
            "priority": self.priority,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data):
        """Build a Task from a dictionary loaded from JSON.

        Raises TaskValidationError (or ValueError/TypeError) if the data is invalid.
        """
        if not isinstance(data, dict):
            raise TaskValidationError("Task entry is not an object.")
        try:
            task_id = int(data["id"])
        except (KeyError, TypeError, ValueError):
            raise TaskValidationError("Task entry has no valid id.")

        cleaned = validate_task_fields(
            title=data.get("title", ""),
            description=data.get("description", ""),
            subject=data.get("subject", ""),
            due_date=data.get("due_date", ""),
            priority=data.get("priority", "Medium"),
            status=data.get("status", "Pending"),
        )
        return cls(task_id=task_id, **cleaned)


class TaskManager:
    """Keeps the list of tasks and provides every action the app needs."""

    def __init__(self, tasks=None):
        self.tasks = []
        self._next_id = 1
        for task in tasks or []:
            # Make sure every loaded task has a unique id
            if self.find_task(task.task_id) is not None:
                task.task_id = self._next_id
            self.tasks.append(task)
            self._next_id = max(self._next_id, task.task_id + 1)

    # ----- Basic lookups -------------------------------------------------
    def find_task(self, task_id):
        """Return the task with this id, or None if it does not exist."""
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        return None

    def _require_task(self, task_id):
        task = self.find_task(task_id)
        if task is None:
            raise KeyError(f"No task with id {task_id} exists.")
        return task

    # ----- Add / edit / delete / complete ---------------------------------
    def add_task(self, title, description="", subject="", due_date="",
                 priority="Medium", status="Pending"):
        """Validate the fields, create a new task and return it."""
        cleaned = validate_task_fields(title, description, subject, due_date, priority, status)
        new_task = Task(task_id=self._next_id, **cleaned)
        self._next_id += 1
        self.tasks.append(new_task)
        return new_task

    def edit_task(self, task_id, **changes):
        """Update the given fields of a task. Validation happens before any change."""
        task = self._require_task(task_id)
        current = {
            "title": task.title,
            "description": task.description,
            "subject": task.subject,
            "due_date": task.due_date,
            "priority": task.priority,
            "status": task.status,
        }
        unknown = set(changes) - set(current)
        if unknown:
            raise TaskValidationError(f"Unknown task field(s): {', '.join(sorted(unknown))}")
        current.update(changes)
        cleaned = validate_task_fields(**current)  # raises before anything is changed
        for field_name, value in cleaned.items():
            setattr(task, field_name, value)
        return task

    def delete_task(self, task_id):
        """Remove a task and return it."""
        task = self._require_task(task_id)
        self.tasks.remove(task)
        return task

    def complete_task(self, task_id, completed=True):
        """Mark a task as Completed (or back to Pending when completed=False)."""
        task = self._require_task(task_id)
        task.status = "Completed" if completed else "Pending"
        return task

    # ----- Dashboard -----------------------------------------------------
    def get_statistics(self, today=None):
        """Return the numbers shown on the dashboard."""
        today = today or date.today()
        completed = sum(1 for task in self.tasks if task.is_completed())
        return {
            "total": len(self.tasks),
            "pending": len(self.tasks) - completed,
            "completed": completed,
            "overdue": sum(1 for task in self.tasks if task.is_overdue(today)),
        }

    # ----- Listing, filtering, searching and sorting ----------------------
    def show_tasks(self, status_filter="All", priority_filter="All", search_text="",
                   sort_ascending=True):
        """Return the tasks that match the filters, sorted by due date.

        Ties on the due date are broken by priority (High first).
        """
        search = search_text.strip().lower()
        matching = []
        for task in self.tasks:
            if status_filter != "All" and task.status != status_filter:
                continue
            if priority_filter != "All" and task.priority != priority_filter:
                continue
            if search and search not in task.title.lower() and search not in task.subject.lower():
                continue
            matching.append(task)

        # Sort by due date first, then by priority (higher priority first on ties)
        matching.sort(
            key=lambda task: (task.due_date_value(), -PRIORITY_RANK[task.priority], task.title.lower())
        )
        if not sort_ascending:
            matching.reverse()
        return matching
