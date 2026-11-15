"""
main.py - TaskMate, a student task manager with a Tkinter interface.

Run with:  python main.py

The interface only handles user interaction. All task rules live in
task_manager.py and all file reading/writing lives in storage.py.
"""

import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

import storage
from task_manager import (
    DATE_FORMAT,
    PRIORITIES,
    STATUSES,
    TaskManager,
    TaskValidationError,
    validate_task_fields,
)

APP_NAME = "TaskMate"
APP_SUBTITLE = "Student Task Manager"
WINDOW_SIZE = "1120x720"
MIN_WINDOW_SIZE = (940, 600)

# Blue and white colour scheme
COLORS = {
    "primary": "#1565C0",
    "primary_dark": "#0D47A1",
    "primary_light": "#E3F2FD",
    "background": "#F4F7FB",
    "card": "#FFFFFF",
    "text": "#1F2A37",
    "muted": "#6B7280",
    "border": "#D6E2F0",
    "warning": "#EF6C00",
    "danger": "#C62828",
    "success": "#2E7D32",
    "disabled": "#90CAF9",
}
FONT_FAMILY = "Segoe UI"  # Standard Windows font; Tk falls back on other systems

FILTER_ALL = "All"


def format_due_date_for_display(due_date_text):
    """Show the due date in a friendly form, e.g. 'Mon, 14 Dec 2026'."""
    try:
        return date.fromisoformat(due_date_text).strftime("%a, %d %b %Y")
    except ValueError:
        return due_date_text


class TaskDialog:
    """A small pop-up window used to add or edit a task.

    After the window closes, self.result holds the cleaned field values,
    or None if the user cancelled.
    """

    def __init__(self, parent, heading, task=None):
        self.result = None
        self.window = tk.Toplevel(parent)
        self.window.title(heading)
        self.window.configure(bg=COLORS["card"])
        self.window.transient(parent)
        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Pre-fill the form with the existing task, or sensible defaults for a new one
        if task is None:
            initial = {
                "title": "", "subject": "", "due_date": date.today().strftime(DATE_FORMAT),
                "priority": "Medium", "status": "Pending", "description": "",
            }
        else:
            initial = {
                "title": task.title, "subject": task.subject, "due_date": task.due_date,
                "priority": task.priority, "status": task.status, "description": task.description,
            }

        self.title_var = tk.StringVar(value=initial["title"])
        self.subject_var = tk.StringVar(value=initial["subject"])
        self.due_var = tk.StringVar(value=initial["due_date"])
        self.priority_var = tk.StringVar(value=initial["priority"])
        self.status_var = tk.StringVar(value=initial["status"])

        body = ttk.Frame(self.window, style="Card.TFrame", padding=(24, 20))
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)

        ttk.Label(body, text=heading, style="DialogTitle.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        self.title_entry = ttk.Entry(body, textvariable=self.title_var, width=42)
        self._add_row(body, 1, "Title *", self.title_entry)
        self.subject_entry = ttk.Entry(body, textvariable=self.subject_var)
        self._add_row(body, 2, "Subject", self.subject_entry)

        due_entry = ttk.Entry(body, textvariable=self.due_var)
        self._add_row(body, 3, "Due date *", due_entry)
        ttk.Label(body, text="Format: YYYY-MM-DD (example: 2026-12-31)",
                  style="Hint.TLabel").grid(row=4, column=1, sticky="w", pady=(0, 8))

        priority_box = ttk.Combobox(body, textvariable=self.priority_var, values=PRIORITIES,
                                    state="readonly")
        self._add_row(body, 5, "Priority", priority_box)

        status_box = ttk.Combobox(body, textvariable=self.status_var, values=STATUSES,
                                  state="readonly")
        self._add_row(body, 6, "Status", status_box)

        ttk.Label(body, text="Description", style="Field.TLabel").grid(
            row=7, column=0, sticky="nw", padx=(0, 14), pady=(6, 0))
        self.description_text = tk.Text(
            body, width=42, height=5, wrap="word", relief="solid", borderwidth=1,
            highlightthickness=0, font=(FONT_FAMILY, 10), padx=6, pady=6)
        self.description_text.grid(row=7, column=1, sticky="ew", pady=(6, 0))
        self.description_text.insert("1.0", initial["description"])

        button_row = ttk.Frame(body, style="Card.TFrame")
        button_row.grid(row=8, column=0, columnspan=2, sticky="e", pady=(22, 0))
        ttk.Button(button_row, text="Cancel", command=self._on_cancel).pack(side="right", padx=(8, 0))
        ttk.Button(button_row, text="Save Task", style="Accent.TButton",
                   command=self._on_save).pack(side="right")

        # Enter saves from the single-line fields; Enter in the description adds a new line
        for entry in (self.title_entry, self.subject_entry, due_entry):
            entry.bind("<Return>", lambda event: self._on_save())
        self.window.bind("<Escape>", lambda event: self._on_cancel())

        # Make the dialog modal: the main window waits until it is closed
        self.window.grab_set()
        self.window.focus_set()
        self.window.update_idletasks()
        self._center_over(parent)

    def _add_row(self, parent, row, label_text, widget):
        ttk.Label(parent, text=label_text, style="Field.TLabel").grid(
            row=row, column=0, sticky="w", padx=(0, 14), pady=6)
        widget.grid(row=row, column=1, sticky="ew", pady=6, ipady=3)

    def _center_over(self, parent):
        self.window.update_idletasks()
        width = self.window.winfo_reqwidth()
        height = self.window.winfo_reqheight()
        x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - height) // 3
        self.window.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _on_save(self):
        description = self.description_text.get("1.0", "end-1c")
        try:
            self.result = validate_task_fields(
                title=self.title_var.get(),
                description=description,
                subject=self.subject_var.get(),
                due_date=self.due_var.get(),
                priority=self.priority_var.get(),
                status=self.status_var.get(),
            )
        except TaskValidationError as error:
            # Keep the dialog open so the user can correct the value
            messagebox.showerror("Invalid input", str(error), parent=self.window)
            return
        self.window.grab_release()
        self.window.destroy()

    def _on_cancel(self):
        self.result = None
        self.window.grab_release()
        self.window.destroy()

    def show(self):
        """Wait until the dialog is closed and return the result."""
        self.window.wait_window()
        return self.result


class TaskMateApp:
    """The main application window."""

    def __init__(self, root):
        self.root = root
        self.data_path = storage.get_default_data_path()

        self.root.title(f"{APP_NAME} - {APP_SUBTITLE}")
        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(*MIN_WINDOW_SIZE)
        self.root.configure(bg=COLORS["background"])

        # Load saved tasks (never crashes on missing or broken files)
        loaded_tasks, load_warning = storage.load_tasks(self.data_path)
        self.manager = TaskManager(loaded_tasks)

        # Filter and sort settings shown in the toolbar
        self.status_filter_var = tk.StringVar(value=FILTER_ALL)
        self.priority_filter_var = tk.StringVar(value=FILTER_ALL)
        self.search_var = tk.StringVar(value="")
        self.sort_ascending = True
        self.sort_button_text = tk.StringVar()

        self._configure_styles()
        self._build_header()
        self._build_dashboard()
        self._build_toolbar()
        self._build_task_table()
        self._build_action_bar()
        self._build_status_bar()

        # Refresh the list whenever a filter or the search text changes
        self.search_var.trace_add("write", lambda *args: self.show_tasks())
        self.status_box.bind("<<ComboboxSelected>>", lambda event: self.show_tasks())
        self.priority_box.bind("<<ComboboxSelected>>", lambda event: self.show_tasks())

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.show_tasks()

        if load_warning:
            messagebox.showwarning("Data warning", load_warning, parent=self.root)

    # ----- Styling -------------------------------------------------------
    def _configure_styles(self):
        """Set up the colours and fonts used by the ttk widgets."""
        style = ttk.Style(self.root)
        style.theme_use("clam")  # 'clam' theme allows custom colours on all systems

        style.configure(".", font=(FONT_FAMILY, 10))
        style.configure("TFrame", background=COLORS["background"])
        style.configure("Card.TFrame", background=COLORS["card"])
        style.configure("TLabel", background=COLORS["background"], foreground=COLORS["text"])
        style.configure("Field.TLabel", background=COLORS["card"], foreground=COLORS["text"],
                        font=(FONT_FAMILY, 10, "bold"))
        style.configure("Hint.TLabel", background=COLORS["card"], foreground=COLORS["muted"],
                        font=(FONT_FAMILY, 8))
        style.configure("DialogTitle.TLabel", background=COLORS["card"],
                        foreground=COLORS["primary_dark"], font=(FONT_FAMILY, 15, "bold"))
        style.configure("Muted.TLabel", background=COLORS["background"],
                        foreground=COLORS["muted"], font=(FONT_FAMILY, 9))
        style.configure("Toolbar.TLabel", background=COLORS["card"], foreground=COLORS["text"],
                        font=(FONT_FAMILY, 10, "bold"))

        style.configure("TButton", padding=(12, 6), background=COLORS["card"],
                        foreground=COLORS["text"], bordercolor=COLORS["border"])
        style.map("TButton", background=[("active", COLORS["primary_light"])])

        style.configure("Accent.TButton", background=COLORS["primary"], foreground="white",
                        font=(FONT_FAMILY, 10, "bold"), padding=(14, 7), borderwidth=0)
        style.map("Accent.TButton",
                  background=[("active", COLORS["primary_dark"]), ("disabled", COLORS["disabled"])],
                  foreground=[("disabled", "white")])

        style.configure("Danger.TButton", background=COLORS["danger"], foreground="white",
                        font=(FONT_FAMILY, 10, "bold"), padding=(14, 7), borderwidth=0)
        style.map("Danger.TButton", background=[("active", "#9A1F1F"), ("disabled", "#EF9A9A")])

        style.configure("TEntry", padding=6, fieldbackground="white", bordercolor=COLORS["border"])
        style.configure("TCombobox", padding=5, fieldbackground="white",
                        bordercolor=COLORS["border"])

        style.configure("Treeview", background="white", fieldbackground="white",
                        foreground=COLORS["text"], rowheight=30, bordercolor=COLORS["border"],
                        font=(FONT_FAMILY, 10))
        style.configure("Treeview.Heading", background=COLORS["primary_light"],
                        foreground=COLORS["primary_dark"], font=(FONT_FAMILY, 10, "bold"),
                        padding=(8, 6), relief="flat")
        style.map("Treeview", background=[("selected", COLORS["primary"])],
                  foreground=[("selected", "white")])
        style.map("Treeview.Heading", background=[("active", COLORS["border"])])

    # ----- Layout --------------------------------------------------------
    def _build_header(self):
        header = tk.Frame(self.root, bg=COLORS["primary"], padx=24, pady=14)
        header.pack(fill="x")
        tk.Label(header, text=APP_NAME, bg=COLORS["primary"], fg="white",
                 font=(FONT_FAMILY, 20, "bold")).pack(side="left")
        tk.Label(header, text=f"  |  {APP_SUBTITLE}", bg=COLORS["primary"], fg="#BBDEFB",
                 font=(FONT_FAMILY, 11)).pack(side="left", pady=(6, 0))
        tk.Label(header, text=date.today().strftime("%A, %d %B %Y"), bg=COLORS["primary"],
                 fg="#BBDEFB", font=(FONT_FAMILY, 10)).pack(side="right", pady=(6, 0))

    def _build_dashboard(self):
        """Create the four statistic cards: Total, Pending, Completed, Overdue."""
        dashboard = ttk.Frame(self.root, padding=(20, 16, 20, 4))
        dashboard.pack(fill="x")
        self.stat_labels = {}
        cards = [
            ("total", "TOTAL TASKS", COLORS["primary"]),
            ("pending", "PENDING", COLORS["warning"]),
            ("completed", "COMPLETED", COLORS["success"]),
            ("overdue", "OVERDUE", COLORS["danger"]),
        ]
        for column_index, (key, caption, colour) in enumerate(cards):
            card = tk.Frame(dashboard, bg=COLORS["card"], highlightthickness=1,
                            highlightbackground=COLORS["border"], padx=18, pady=12)
            card.grid(row=0, column=column_index, sticky="nsew",
                      padx=(0 if column_index == 0 else 12, 0))
            dashboard.columnconfigure(column_index, weight=1, uniform="cards")
            tk.Label(card, text=caption, bg=COLORS["card"], fg=COLORS["muted"],
                     font=(FONT_FAMILY, 9, "bold")).pack(anchor="w")
            value_label = tk.Label(card, text="0", bg=COLORS["card"], fg=colour,
                                   font=(FONT_FAMILY, 24, "bold"))
            value_label.pack(anchor="w")
            self.stat_labels[key] = value_label

    def _build_toolbar(self):
        """Search box plus filter and sort controls."""
        toolbar = tk.Frame(self.root, bg=COLORS["card"], highlightthickness=1,
                           highlightbackground=COLORS["border"], padx=14, pady=10)
        toolbar.pack(fill="x", padx=20, pady=(10, 8))

        tk.Label(toolbar, text="Search", bg=COLORS["card"], fg=COLORS["text"],
                 font=(FONT_FAMILY, 10, "bold")).pack(side="left")
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=28)
        search_entry.pack(side="left", padx=(8, 4), ipady=2)
        search_entry.bind("<Escape>", lambda event: self.search_var.set(""))

        tk.Label(toolbar, text="Status", bg=COLORS["card"], fg=COLORS["text"],
                 font=(FONT_FAMILY, 10, "bold")).pack(side="left", padx=(18, 6))
        self.status_box = ttk.Combobox(toolbar, textvariable=self.status_filter_var,
                                       values=[FILTER_ALL, *STATUSES], state="readonly", width=12)
        self.status_box.pack(side="left")

        tk.Label(toolbar, text="Priority", bg=COLORS["card"], fg=COLORS["text"],
                 font=(FONT_FAMILY, 10, "bold")).pack(side="left", padx=(18, 6))
        self.priority_box = ttk.Combobox(toolbar, textvariable=self.priority_filter_var,
                                         values=[FILTER_ALL, *PRIORITIES], state="readonly", width=10)
        self.priority_box.pack(side="left")

        ttk.Button(toolbar, text="Clear Filters", command=self.clear_filters).pack(side="right")
        ttk.Button(toolbar, textvariable=self.sort_button_text,
                   command=self.toggle_sort).pack(side="right", padx=(0, 10))
        self._update_sort_button_text()

    def _build_task_table(self):
        table_frame = ttk.Frame(self.root)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 6))

        columns = ("title", "subject", "due", "priority", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                 selectmode="browse")
        headings = {"title": "Title", "subject": "Subject", "due": "Due Date",
                    "priority": "Priority", "status": "Status"}
        widths = {"title": 340, "subject": 170, "due": 150, "priority": 100, "status": 110}
        for column in columns:
            self.tree.heading(column, text=headings[column], anchor="w")
            self.tree.column(column, width=widths[column], anchor="w", stretch=column == "title")

        # Colour tags: overdue tasks in red, completed tasks in grey
        self.tree.tag_configure("overdue", foreground=COLORS["danger"])
        self.tree.tag_configure("completed", foreground=COLORS["muted"])

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda event: self.edit_task())
        self.tree.bind("<Return>", lambda event: self.edit_task())
        self.tree.bind("<Delete>", lambda event: self.delete_task())
        self.tree.bind("<<TreeviewSelect>>", lambda event: self._update_action_buttons())

    def _build_action_bar(self):
        action_bar = ttk.Frame(self.root)
        action_bar.pack(fill="x", padx=20, pady=(4, 8))

        ttk.Button(action_bar, text="+ Add Task", style="Accent.TButton",
                   command=self.add_task).pack(side="left")
        ttk.Button(action_bar, text="Edit Task", command=self.edit_task).pack(side="left", padx=(10, 0))
        self.complete_button = ttk.Button(action_bar, text="Mark Complete",
                                          command=self.complete_task)
        self.complete_button.pack(side="left", padx=(10, 0))
        ttk.Button(action_bar, text="Delete Task", style="Danger.TButton",
                   command=self.delete_task).pack(side="left", padx=(10, 0))

        ttk.Label(action_bar, text="Changes are saved automatically.",
                  style="Muted.TLabel").pack(side="right")

    def _build_status_bar(self):
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, style="Muted.TLabel",
                               padding=(20, 0, 20, 10))
        status_bar.pack(fill="x", side="bottom")

    # ----- Actions -------------------------------------------------------
    def _selected_task_id(self):
        """Return the id of the selected task, or None (and show a message)."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("No task selected", "Please select a task in the list first.",
                                parent=self.root)
            return None
        return int(selection[0])

    def save_tasks(self):
        """Write all tasks to the JSON file. Returns True if saving worked."""
        try:
            storage.save_tasks(self.manager.tasks, self.data_path)
            return True
        except OSError as error:
            messagebox.showerror("Save failed",
                                 f"TaskMate could not save your tasks.\n\n{error}",
                                 parent=self.root)
            return False

    def show_tasks(self):
        """Refresh the task list, dashboard and status bar using the current filters."""
        previously_selected = self.tree.selection()

        self.tree.delete(*self.tree.get_children())
        today = date.today()
        visible_tasks = self.manager.show_tasks(
            status_filter=self.status_filter_var.get(),
            priority_filter=self.priority_filter_var.get(),
            search_text=self.search_var.get(),
            sort_ascending=self.sort_ascending,
        )
        for task in visible_tasks:
            tags = []
            if task.is_overdue(today):
                tags.append("overdue")
            elif task.is_completed():
                tags.append("completed")
            self.tree.insert("", "end", iid=str(task.task_id), tags=tags, values=(
                task.title,
                task.subject or "-",
                format_due_date_for_display(task.due_date),
                task.priority,
                task.status,
            ))

        # Keep the previously selected task highlighted if it is still visible
        for item_id in previously_selected:
            if self.tree.exists(item_id):
                self.tree.selection_set(item_id)
                self.tree.see(item_id)

        self._update_dashboard()
        total = len(self.manager.tasks)
        self.status_var.set(f"Showing {len(visible_tasks)} of {total} task(s).   "
                            f"Data file: {self.data_path}")
        self._update_action_buttons()

    def _update_dashboard(self):
        stats = self.manager.get_statistics()
        for key, label in self.stat_labels.items():
            label.config(text=str(stats[key]))

    def _update_action_buttons(self):
        """Change the complete button text to match the selected task."""
        selection = self.tree.selection()
        task = self.manager.find_task(int(selection[0])) if selection else None
        if task is not None and task.is_completed():
            self.complete_button.config(text="Mark Pending")
        else:
            self.complete_button.config(text="Mark Complete")

    def _update_sort_button_text(self):
        arrow = "▲" if self.sort_ascending else "▼"
        self.sort_button_text.set(f"Due Date {arrow}")

    def toggle_sort(self):
        self.sort_ascending = not self.sort_ascending
        self._update_sort_button_text()
        self.show_tasks()

    def clear_filters(self):
        self.status_filter_var.set(FILTER_ALL)
        self.priority_filter_var.set(FILTER_ALL)
        self.search_var.set("")
        self.show_tasks()

    def add_task(self):
        """Open the form to create a new task, then save and refresh."""
        dialog = TaskDialog(self.root, "Add New Task")
        values = dialog.show()
        if values is None:
            return
        try:
            new_task = self.manager.add_task(**values)
        except TaskValidationError as error:
            messagebox.showerror("Invalid input", str(error), parent=self.root)
            return
        self.save_tasks()
        self.show_tasks()
        self._select_task(new_task.task_id)

    def edit_task(self):
        """Open the form filled with the selected task, then save the changes."""
        task_id = self._selected_task_id()
        if task_id is None:
            return
        task = self.manager.find_task(task_id)
        if task is None:
            return
        dialog = TaskDialog(self.root, "Edit Task", task=task)
        values = dialog.show()
        if values is None:
            return
        try:
            self.manager.edit_task(task_id, **values)
        except TaskValidationError as error:
            messagebox.showerror("Invalid input", str(error), parent=self.root)
            return
        self.save_tasks()
        self.show_tasks()
        self._select_task(task_id)

    def delete_task(self):
        """Delete the selected task after the user confirms."""
        task_id = self._selected_task_id()
        if task_id is None:
            return
        task = self.manager.find_task(task_id)
        if task is None:
            return
        confirmed = messagebox.askyesno(
            "Delete task",
            f"Delete the task '{task.title}'?\n\nThis cannot be undone.",
            parent=self.root)
        if not confirmed:
            return
        self.manager.delete_task(task_id)
        self.save_tasks()
        self.show_tasks()

    def complete_task(self):
        """Toggle the selected task between Completed and Pending."""
        task_id = self._selected_task_id()
        if task_id is None:
            return
        task = self.manager.find_task(task_id)
        if task is None:
            return
        self.manager.complete_task(task_id, completed=not task.is_completed())
        self.save_tasks()
        self.show_tasks()

    def _select_task(self, task_id):
        """Highlight a task in the list if it is visible with the current filters."""
        item_id = str(task_id)
        if self.tree.exists(item_id):
            self.tree.selection_set(item_id)
            self.tree.see(item_id)

    def on_close(self):
        """Save once more before closing the window."""
        self.save_tasks()
        self.root.destroy()


def main():
    root = tk.Tk()
    TaskMateApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
