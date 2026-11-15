# TaskMate – Student Task Manager

TaskMate is a simple desktop application that helps students keep track of
homework, assignments, exams and daily tasks. It is written in Python with a
Tkinter graphical interface and stores everything in a local JSON file.

It uses only the Python standard library: no internet connection, no database
server, no paid services and no extra packages.

## Features

- **Task management** – add, edit, delete and mark tasks as completed (and back to pending).
- **Task details** – title, description, subject, due date, priority (Low / Medium / High) and status (Pending / Completed).
- **Dashboard** – total, pending, completed and overdue task counts at a glance.
- **Organisation** – filter by status and priority, search by title or subject, and sort by due date (ascending or descending).
- **Validation** – empty titles, invalid dates and invalid choices are rejected with a clear message.
- **Automatic saving** – every change is saved to `tasks.json` immediately and loaded again when the app starts.
- **Arabic and English** – switch the whole interface between English and العربية (with right-to-left layout for Arabic) from the drop-down at the top right. Your choice is remembered.
- **Safe data handling** – a missing file starts an empty list; a damaged file is backed up (renamed with a `.corrupt-` timestamp) instead of crashing the app. If only some saved tasks are invalid, the valid ones load and a copy of the original file is kept before anything is rewritten.

## Technologies Used

- Python 3 (standard library only)
- Tkinter and `ttk` for the graphical interface
- `json` for local data storage
- `unittest` for the automated tests

## Project Structure

```
TaskMate/
├── main.py             # Application entry point and the Tkinter window
├── task_manager.py     # Task model, validation, add/edit/delete/complete, filter/sort, statistics
├── storage.py          # Loading and saving tasks.json and settings.json safely
├── i18n.py             # English and Arabic text
├── tasks.json          # Local task data file (created/updated by the app)
├── settings.json       # Remembered language (created when you change the language)
├── tests/
│   └── test_taskmate.py  # Automated tests for the logic, storage and translations
├── .gitignore
└── README.md
```

## Installation (Windows)

1. Install **Python 3.9 or newer** from <https://www.python.org/downloads/>.
   During installation, tick **"Add python.exe to PATH"**, and keep the
   default **"tcl/tk and IDLE"** option ticked (it provides Tkinter).
2. Download or clone this repository, for example:
   ```bat
   git clone https://github.com/Wellyer/TaskMate.git
   cd TaskMate
   ```
   or download the ZIP from GitHub and extract it.

No other installation is needed.

## How to Run

Open **Command Prompt** or **PowerShell** in the `TaskMate` folder and run:

```bat
python main.py
```

(If `python` is not recognised, try `py main.py`.)

To run the automated tests (these do not open the window):

```bat
python -m unittest discover -s tests -v
```

## Example Usage

1. Click **+ Add Task**.
2. Fill in the form, for example:
   - Title: `Write history essay`
   - Subject: `History`
   - Due date: `2026-12-01` (format `YYYY-MM-DD`)
   - Priority: `High`
   - Description: `Two pages about the Industrial Revolution`
3. Click **Save Task**. The task appears in the list and the dashboard updates.
4. Select a task and click **Mark Complete** when it is finished. Click it again (now labelled **Mark Pending**) to reopen it.
5. Double-click a task (or select it and click **Edit Task**) to change it.
6. Select a task and click **Delete Task** (or press the Delete key) to remove it after confirmation.
7. Use the **Search** box, the **Status** and **Priority** drop-downs, and the **Due Date** button to find and order your tasks. **Clear Filters** resets everything.

Overdue tasks are shown in red. Completed tasks are shown in grey.

## Changing the Language

Use the **Language** drop-down at the top right of the window to choose
**English** or **العربية**. The window is redrawn immediately, and the choice is
saved in `settings.json`. Task data is stored in English internally, so switching
language never changes your tasks.

## Data File

All tasks are stored in `tasks.json` in the same folder as `main.py`:

```json
{
    "version": 1,
    "tasks": [
        {
            "id": 1,
            "title": "Write history essay",
            "description": "Two pages about the Industrial Revolution",
            "subject": "History",
            "due_date": "2026-12-01",
            "priority": "High",
            "status": "Pending"
        }
    ]
}
```

## Notes

- Deleting a task cannot be undone, so the confirmation message is shown first.
- If `tasks.json` is damaged, the app shows a warning, moves the damaged file to a
  backup named `tasks.corrupt-<date-time>.json`, and starts with an empty list.
- If some tasks in `tasks.json` are invalid, the valid tasks are loaded, a copy of the
  original file is saved as `tasks.invalid-backup-<date-time>.json`, and a warning is shown.
