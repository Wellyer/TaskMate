"""
main.py - TaskMate, a student task manager with a Tkinter interface.

Run with:  python main.py

The interface only handles user interaction and layout. All task rules live
in task_manager.py, all file reading/writing lives in storage.py, and all
visible text comes from i18n.py (English and Arabic).
"""

import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

import i18n
import storage
from i18n import LANGUAGES, t
from task_manager import (
    DATE_FORMAT,
    PRIORITIES,
    STATUSES,
    TaskManager,
    TaskValidationError,
    validate_task_fields,
)

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
FONT_FAMILY = "Segoe UI"  # Standard Windows font (supports Arabic); Tk falls back elsewhere

FILTER_ALL = "All"  # internal value meaning "no filter"
TABLE_COLUMNS = ("title", "subject", "due", "priority", "status")
ARROW_UP = "▲"
ARROW_DOWN = "▼"


# ----- Small helpers for layout and language ---------------------------
def start_side():
    """'left' normally, 'right' in Arabic (where the reading start is on the right)."""
    return "right" if i18n.is_rtl() else "left"


def end_side():
    return "left" if i18n.is_rtl() else "right"


def text_anchor():
    return "e" if i18n.is_rtl() else "w"


def text_justify():
    return "right" if i18n.is_rtl() else "left"


def priority_label(key):
    return t(f"priority_{key}")


def status_label(key):
    return t(f"status_{key}")


def error_text(error):
    """Turn a TaskValidationError into a message in the current language."""
    return t(error.key, **error.params)


def notice_text(notice):
    """Turn a storage Notice into a message in the current language."""
    params = dict(notice.params)
    if "backup_path" in params:
        backup_path = params.pop("backup_path")
        params["backup_note"] = t("warn_backup_note", path=backup_path) if backup_path else ""
    return t(notice.key, **params)


class TaskDialog:
    """A pop-up window used to add or edit a task.

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

        body = ttk.Frame(self.window, style="Card.TFrame", padding=(24, 20))
        body.pack(fill="both", expand=True)
        # In Arabic the labels sit on the right and the inputs on the left
        self.label_column = 1 if i18n.is_rtl() else 0
        self.input_column = 0 if i18n.is_rtl() else 1
        body.columnconfigure(self.input_column, weight=1)

        ttk.Label(body, text=heading, style="DialogTitle.TLabel").grid(
            row=0, column=0, columnspan=2, sticky=text_anchor(), pady=(0, 14))

        self.title_entry = ttk.Entry(body, textvariable=self.title_var, width=42,
                                     justify=text_justify())
        self._add_row(body, 1, t("field_title"), self.title_entry)
        self.subject_entry = ttk.Entry(body, textvariable=self.subject_var,
                                       justify=text_justify())
        self._add_row(body, 2, t("field_subject"), self.subject_entry)

        self.due_entry = ttk.Entry(body, textvariable=self.due_var, justify=text_justify())
        self._add_row(body, 3, t("field_due"), self.due_entry)
        ttk.Label(body, text=t("due_hint"), style="Hint.TLabel").grid(
            row=4, column=self.input_column, sticky=text_anchor(), pady=(0, 8))

        self.priority_box = ttk.Combobox(body, values=[priority_label(p) for p in PRIORITIES],
                                         state="readonly", justify=text_justify())
        self.priority_box.current(PRIORITIES.index(initial["priority"]))
        self._add_row(body, 5, t("field_priority"), self.priority_box)

        self.status_box = ttk.Combobox(body, values=[status_label(s) for s in STATUSES],
                                       state="readonly", justify=text_justify())
        self.status_box.current(STATUSES.index(initial["status"]))
        self._add_row(body, 6, t("field_status"), self.status_box)

        ttk.Label(body, text=t("field_description"), style="Field.TLabel").grid(
            row=7, column=self.label_column, sticky="n" if not i18n.is_rtl() else "ne",
            padx=(0, 14) if not i18n.is_rtl() else (14, 0), pady=(6, 0))
        self.description_text = tk.Text(
            body, width=42, height=5, wrap="word", relief="solid", borderwidth=1,
            highlightthickness=0, font=(FONT_FAMILY, 10), padx=6, pady=6)
        self.description_text.grid(row=7, column=self.input_column, sticky="ew", pady=(6, 0))
        self.description_text.insert("1.0", initial["description"])
        self.description_text.tag_configure("align", justify=text_justify())
        self.description_text.tag_add("align", "1.0", "end")

        button_row = ttk.Frame(body, style="Card.TFrame")
        button_row.grid(row=8, column=0, columnspan=2, sticky="e" if not i18n.is_rtl() else "w",
                        pady=(22, 0))
        ttk.Button(button_row, text=t("cancel"), command=self._on_cancel).pack(
            side=end_side(), padx=(8, 0))
        ttk.Button(button_row, text=t("save_task"), style="Accent.TButton",
                   command=self._on_save).pack(side=start_side())

        # Enter saves from the single-line fields; Enter in the description adds a new line
        for entry in (self.title_entry, self.subject_entry, self.due_entry):
            entry.bind("<Return>", lambda event: self._on_save())
        self.window.bind("<Escape>", lambda event: self._on_cancel())

        # Show the dialog, then make it modal so the main window waits for it
        self.window.update_idletasks()
        self._center_over(parent)
        self.window.wait_visibility()
        self.window.grab_set()
        self.window.focus_set()

    def _add_row(self, parent, row, label_text, widget):
        ttk.Label(parent, text=label_text, style="Field.TLabel").grid(
            row=row, column=self.label_column, sticky=text_anchor(),
            padx=(0, 14) if not i18n.is_rtl() else (14, 0), pady=6)
        widget.grid(row=row, column=self.input_column, sticky="ew", pady=6, ipady=3)

    def _center_over(self, parent):
        width = self.window.winfo_reqwidth()
        height = self.window.winfo_reqheight()
        x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - height) // 3
        self.window.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _on_save(self):
        description = self.description_text.get("1.0", "end-1c")
        priority_index = self.priority_box.current()
        status_index = self.status_box.current()
        try:
            self.result = validate_task_fields(
                title=self.title_var.get(),
                description=description,
                subject=self.subject_var.get(),
                due_date=self.due_entry.get(),
                priority=PRIORITIES[priority_index] if priority_index >= 0 else "Medium",
                status=STATUSES[status_index] if status_index >= 0 else "Pending",
            )
        except TaskValidationError as error:
            # Keep the dialog open so the user can correct the value
            messagebox.showerror(t("title_invalid_input"), error_text(error), parent=self.window)
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

        # Use the language the user chose last time
        self.language = storage.load_language()
        i18n.set_language(self.language)

        # Load saved tasks (never crashes on missing or broken files)
        loaded_tasks, load_notice = storage.load_tasks(self.data_path)
        self.manager = TaskManager(loaded_tasks)

        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(*MIN_WINDOW_SIZE)

        # Filter and sort settings. Filters hold internal values (e.g. "Pending"),
        # never translated text, so they work in every language.
        self.status_filter = FILTER_ALL
        self.priority_filter = FILTER_ALL
        self.search_var = tk.StringVar(value="")
        self.sort_ascending = True
        self.sort_button_text = tk.StringVar()

        self._configure_styles()
        self.build_ui()

        # Refresh the list whenever the search text changes
        self.search_var.trace_add("write", lambda *args: self.show_tasks())
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.show_tasks()

        if load_notice:
            messagebox.showwarning(t("title_data_warning"), notice_text(load_notice),
                                   parent=self.root)

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
    def build_ui(self):
        """(Re)build every widget using the current language and direction.

        Called at startup and again whenever the language is changed.
        """
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.title(f"{t('app_name')} - {t('app_subtitle')}")
        self.root.configure(bg=COLORS["background"])

        self._build_header()
        self._build_dashboard()
        self._build_toolbar()
        self._build_task_table()
        self._build_action_bar()
        self._build_status_bar()
        self.show_tasks()

    def _build_header(self):
        header = tk.Frame(self.root, bg=COLORS["primary"], padx=24, pady=14)
        header.pack(fill="x")

        brand = tk.Frame(header, bg=COLORS["primary"])
        brand.pack(side=start_side())
        tk.Label(brand, text=t("app_name"), bg=COLORS["primary"], fg="white",
                 font=(FONT_FAMILY, 20, "bold")).pack(side=start_side())
        tk.Label(brand, text=f"  |  {t('app_subtitle')}", bg=COLORS["primary"], fg="#BBDEFB",
                 font=(FONT_FAMILY, 11)).pack(side=start_side(), pady=(6, 0))

        right = tk.Frame(header, bg=COLORS["primary"])
        right.pack(side=end_side())
        tk.Label(right, text=date.today().isoformat(), bg=COLORS["primary"],
                 fg="#BBDEFB", font=(FONT_FAMILY, 10)).pack(side=end_side(), pady=(6, 0), padx=(18, 0))

        # Language choice: names are always shown in their own language
        codes = list(LANGUAGES)
        self.language_box = ttk.Combobox(right, values=[LANGUAGES[code] for code in codes],
                                         state="readonly", width=10)
        self.language_box.current(codes.index(self.language))
        self.language_box.pack(side=end_side())
        self.language_box.bind("<<ComboboxSelected>>",
                               lambda event: self.change_language(codes[self.language_box.current()]))

    def _build_dashboard(self):
        """Create the four statistic cards: Total, Pending, Completed, Overdue."""
        dashboard = ttk.Frame(self.root, padding=(20, 16, 20, 4))
        dashboard.pack(fill="x")
        self.stat_labels = {}
        cards = [
            ("total", "stat_total", COLORS["primary"]),
            ("pending", "stat_pending", COLORS["warning"]),
            ("completed", "stat_completed", COLORS["success"]),
            ("overdue", "stat_overdue", COLORS["danger"]),
        ]
        for column_index, (key, caption_key, colour) in enumerate(cards):
            card = tk.Frame(dashboard, bg=COLORS["card"], highlightthickness=1,
                            highlightbackground=COLORS["border"], padx=18, pady=12)
            card.grid(row=0, column=column_index, sticky="nsew",
                      padx=(0 if column_index == 0 else 12, 0))
            dashboard.columnconfigure(column_index, weight=1, uniform="cards")
            tk.Label(card, text=t(caption_key), bg=COLORS["card"], fg=COLORS["muted"],
                     font=(FONT_FAMILY, 9, "bold")).pack(anchor=text_anchor())
            value_label = tk.Label(card, text="0", bg=COLORS["card"], fg=colour,
                                   font=(FONT_FAMILY, 24, "bold"))
            value_label.pack(anchor=text_anchor())
            self.stat_labels[key] = value_label

    def _build_toolbar(self):
        """Search box plus filter and sort controls."""
        toolbar = tk.Frame(self.root, bg=COLORS["card"], highlightthickness=1,
                           highlightbackground=COLORS["border"], padx=14, pady=10)
        toolbar.pack(fill="x", padx=20, pady=(10, 8))

        def label(text, padx=(0, 0)):
            tk.Label(toolbar, text=text, bg=COLORS["card"], fg=COLORS["text"],
                     font=(FONT_FAMILY, 10, "bold")).pack(side=start_side(), padx=padx)

        label(t("search"))
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=28,
                                 justify=text_justify())
        search_entry.pack(side=start_side(), padx=(8, 4), ipady=2)
        search_entry.bind("<Escape>", lambda event: self.search_var.set(""))

        label(t("status"), padx=(18, 6))
        status_keys = [FILTER_ALL, *STATUSES]
        self.status_box = ttk.Combobox(toolbar, values=[t("all")] + [status_label(s) for s in STATUSES],
                                       state="readonly", width=12)
        self.status_box.current(status_keys.index(self.status_filter))
        self.status_box.pack(side=start_side())
        self.status_box.bind("<<ComboboxSelected>>", lambda event: self._on_status_filter(status_keys))

        label(t("priority"), padx=(18, 6))
        priority_keys = [FILTER_ALL, *PRIORITIES]
        self.priority_box = ttk.Combobox(toolbar, values=[t("all")] + [priority_label(p) for p in PRIORITIES],
                                         state="readonly", width=10)
        self.priority_box.current(priority_keys.index(self.priority_filter))
        self.priority_box.pack(side=start_side())
        self.priority_box.bind("<<ComboboxSelected>>", lambda event: self._on_priority_filter(priority_keys))

        ttk.Button(toolbar, text=t("clear_filters"), command=self.clear_filters).pack(side=end_side())
        ttk.Button(toolbar, textvariable=self.sort_button_text,
                   command=self.toggle_sort).pack(side=end_side(), padx=(0, 10))
        self._update_sort_button_text()

    def _build_task_table(self):
        table_frame = ttk.Frame(self.root)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 6))

        # In Arabic the columns run right to left
        columns = self._column_order()
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                 selectmode="browse")
        widths = {"title": 340, "subject": 170, "due": 150, "priority": 100, "status": 110}
        headings = {"title": "col_title", "subject": "col_subject", "due": "col_due",
                    "priority": "col_priority", "status": "col_status"}
        for column in columns:
            self.tree.heading(column, text=t(headings[column]), anchor=text_anchor())
            self.tree.column(column, width=widths[column], anchor=text_anchor(),
                             stretch=column == "title")

        # Colour tags: overdue tasks in red, completed tasks in grey
        self.tree.tag_configure("overdue", foreground=COLORS["danger"])
        self.tree.tag_configure("completed", foreground=COLORS["muted"])

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=start_side(), fill="both", expand=True)
        scrollbar.pack(side=end_side(), fill="y")

        self.tree.bind("<Double-1>", lambda event: self.edit_task())
        self.tree.bind("<Return>", lambda event: self.edit_task())
        self.tree.bind("<Delete>", lambda event: self.delete_task())
        self.tree.bind("<<TreeviewSelect>>", lambda event: self._update_action_buttons())

    def _column_order(self):
        return list(reversed(TABLE_COLUMNS)) if i18n.is_rtl() else list(TABLE_COLUMNS)

    def _build_action_bar(self):
        action_bar = ttk.Frame(self.root)
        action_bar.pack(fill="x", padx=20, pady=(4, 8))

        ttk.Button(action_bar, text=t("add_task"), style="Accent.TButton",
                   command=self.add_task).pack(side=start_side())
        ttk.Button(action_bar, text=t("edit_task"), command=self.edit_task).pack(
            side=start_side(), padx=(10, 0))
        self.complete_button = ttk.Button(action_bar, text=t("mark_complete"),
                                          command=self.complete_task)
        self.complete_button.pack(side=start_side(), padx=(10, 0))
        ttk.Button(action_bar, text=t("delete_task"), style="Danger.TButton",
                   command=self.delete_task).pack(side=start_side(), padx=(10, 0))

        ttk.Label(action_bar, text=t("autosave_note"), style="Muted.TLabel").pack(side=end_side())

    def _build_status_bar(self):
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, style="Muted.TLabel",
                               padding=(20, 0, 20, 10), anchor=text_anchor(),
                               justify=text_justify())
        status_bar.pack(fill="x", side="bottom")

    # ----- Language ------------------------------------------------------
    def change_language(self, code):
        """Switch the interface language, remember it, and redraw the window."""
        i18n.set_language(code)
        self.language = code
        try:
            storage.save_language(code)
        except OSError:
            pass  # The language still changes for this session even if it cannot be remembered
        self.build_ui()

    # ----- Actions -------------------------------------------------------
    def _selected_task_id(self):
        """Return the id of the selected task, or None (and show a message)."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo(t("title_no_selection"), t("msg_no_selection"), parent=self.root)
            return None
        return int(selection[0])

    def _selected_task(self):
        task_id = self._selected_task_id()
        if task_id is None:
            return None
        return self.manager.find_task(task_id)

    def save_tasks(self):
        """Write all tasks to the JSON file. Returns True if saving worked."""
        try:
            storage.save_tasks(self.manager.tasks, self.data_path)
            return True
        except OSError as error:
            messagebox.showerror(t("title_save_failed"), t("msg_save_failed", error=error),
                                 parent=self.root)
            return False

    def show_tasks(self):
        """Refresh the task list, dashboard and status bar using the current filters."""
        if not hasattr(self, "tree"):
            return  # The window is not built yet
        previously_selected = self.tree.selection()

        self.tree.delete(*self.tree.get_children())
        today = date.today()
        visible_tasks = self.manager.show_tasks(
            status_filter=self.status_filter,
            priority_filter=self.priority_filter,
            search_text=self.search_var.get(),
            sort_ascending=self.sort_ascending,
        )
        for task in visible_tasks:
            tags = []
            if task.is_overdue(today):
                tags.append("overdue")
            elif task.is_completed():
                tags.append("completed")
            cells = {
                "title": task.title,
                "subject": task.subject or "-",
                "due": task.due_date,
                "priority": priority_label(task.priority),
                "status": status_label(task.status),
            }
            self.tree.insert("", "end", iid=str(task.task_id), tags=tags,
                             values=[cells[column] for column in self._column_order()])

        # Keep the previously selected task highlighted if it is still visible
        for item_id in previously_selected:
            if self.tree.exists(item_id):
                self.tree.selection_set(item_id)
                self.tree.see(item_id)

        self._update_dashboard()
        self.status_var.set(t("status_bar", shown=len(visible_tasks),
                              total=len(self.manager.tasks), path=self.data_path))
        self._update_action_buttons()

    def _update_dashboard(self):
        stats = self.manager.get_statistics()
        for key, label in self.stat_labels.items():
            label.config(text=str(stats[key]))

    def _update_action_buttons(self):
        """Change the complete button text to match the selected task."""
        task = self._selected_task_for_buttons()
        if task is not None and task.is_completed():
            self.complete_button.config(text=t("mark_pending"))
        else:
            self.complete_button.config(text=t("mark_complete"))

    def _selected_task_for_buttons(self):
        selection = self.tree.selection()
        return self.manager.find_task(int(selection[0])) if selection else None

    def _update_sort_button_text(self):
        arrow = ARROW_UP if self.sort_ascending else ARROW_DOWN
        self.sort_button_text.set(f"{t('sort_due_date')} {arrow}")

    def _on_status_filter(self, status_keys):
        self.status_filter = status_keys[self.status_box.current()]
        self.show_tasks()

    def _on_priority_filter(self, priority_keys):
        self.priority_filter = priority_keys[self.priority_box.current()]
        self.show_tasks()

    def toggle_sort(self):
        self.sort_ascending = not self.sort_ascending
        self._update_sort_button_text()
        self.show_tasks()

    def clear_filters(self):
        self.status_filter = FILTER_ALL
        self.priority_filter = FILTER_ALL
        self.status_box.current(0)
        self.priority_box.current(0)
        self.search_var.set("")
        self.show_tasks()

    def add_task(self):
        """Open the form to create a new task, then save and refresh."""
        dialog = TaskDialog(self.root, t("dialog_add_title"))
        values = dialog.show()
        if values is None:
            return
        try:
            new_task = self.manager.add_task(**values)
        except TaskValidationError as error:
            messagebox.showerror(t("title_invalid_input"), error_text(error), parent=self.root)
            return
        self.save_tasks()
        self.show_tasks()
        self._select_task(new_task.task_id)

    def edit_task(self):
        """Open the form filled with the selected task, then save the changes."""
        task = self._selected_task()
        if task is None:
            return
        dialog = TaskDialog(self.root, t("dialog_edit_title"), task=task)
        values = dialog.show()
        if values is None:
            return
        try:
            self.manager.edit_task(task.task_id, **values)
        except TaskValidationError as error:
            messagebox.showerror(t("title_invalid_input"), error_text(error), parent=self.root)
            return
        self.save_tasks()
        self.show_tasks()
        self._select_task(task.task_id)

    def delete_task(self):
        """Delete the selected task after the user confirms."""
        task = self._selected_task()
        if task is None:
            return
        confirmed = messagebox.askyesno(
            t("title_delete"), t("msg_delete_confirm", title=task.title), parent=self.root)
        if not confirmed:
            return
        self.manager.delete_task(task.task_id)
        self.save_tasks()
        self.show_tasks()

    def complete_task(self):
        """Toggle the selected task between Completed and Pending."""
        task = self._selected_task()
        if task is None:
            return
        self.manager.complete_task(task.task_id, completed=not task.is_completed())
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
