"""
i18n.py - English and Arabic text for TaskMate.

Every piece of text shown to the user comes from the TRANSLATIONS table.
Use t("key") to get the text for the current language, and t("key", name=value)
to fill in placeholders such as {title}.

Task data (priorities, statuses) is always stored in English keys such as
"High" or "Pending" in the JSON file, so changing the language never changes
the saved data.
"""

LANGUAGES = {"en": "English", "ar": "العربية"}
DEFAULT_LANGUAGE = "en"

TRANSLATIONS = {
    "en": {
        # Window and header
        "app_name": "TaskMate",
        "app_subtitle": "Student Task Manager",
        "language_label": "Language",

        # Dashboard cards
        "stat_total": "TOTAL TASKS",
        "stat_pending": "PENDING",
        "stat_completed": "COMPLETED",
        "stat_overdue": "OVERDUE",

        # Toolbar
        "search": "Search",
        "status": "Status",
        "priority": "Priority",
        "all": "All",
        "clear_filters": "Clear Filters",
        "sort_due_date": "Due Date",

        # Table headings
        "col_title": "Title",
        "col_subject": "Subject",
        "col_due": "Due Date",
        "col_priority": "Priority",
        "col_status": "Status",

        # Priority and status values (shown to the user only)
        "priority_Low": "Low",
        "priority_Medium": "Medium",
        "priority_High": "High",
        "status_Pending": "Pending",
        "status_Completed": "Completed",

        # Action buttons
        "add_task": "+ Add Task",
        "edit_task": "Edit Task",
        "mark_complete": "Mark Complete",
        "mark_pending": "Mark Pending",
        "delete_task": "Delete Task",
        "autosave_note": "Changes are saved automatically.",

        # Add / edit dialog
        "dialog_add_title": "Add New Task",
        "dialog_edit_title": "Edit Task",
        "field_title": "Title *",
        "field_subject": "Subject",
        "field_due": "Due date *",
        "due_hint": "Format: YYYY-MM-DD (example: 2026-12-31)",
        "field_priority": "Priority",
        "field_status": "Status",
        "field_description": "Description",
        "save_task": "Save Task",
        "cancel": "Cancel",

        # Status bar
        "status_bar": "Showing {shown} of {total} task(s).   Data file: {path}",

        # Messages
        "title_no_selection": "No task selected",
        "msg_no_selection": "Please select a task in the list first.",
        "title_invalid_input": "Invalid input",
        "title_save_failed": "Save failed",
        "msg_save_failed": "TaskMate could not save your tasks.\n\n{error}",
        "title_delete": "Delete task",
        "msg_delete_confirm": "Delete the task '{title}'?\n\nThis cannot be undone.",
        "title_data_warning": "Data warning",

        # Validation errors
        "err_title_empty": "The task title cannot be empty.",
        "err_title_long": "The title must be {max} characters or fewer.",
        "err_subject_long": "The subject must be {max} characters or fewer.",
        "err_description_long": "The description must be {max} characters or fewer.",
        "err_due_required": "Due date is required (format YYYY-MM-DD).",
        "err_due_invalid": "'{value}' is not a valid due date. Use YYYY-MM-DD, e.g. 2026-12-31.",
        "err_priority": "Priority must be Low, Medium or High.",
        "err_status": "Status must be Pending or Completed.",
        "err_unknown_field": "Unknown task field(s): {fields}",
        "err_task_entry_not_object": "Task entry is not an object.",
        "err_task_id": "Task entry has no valid id.",

        # Data file warnings
        "warn_open_failed": "Could not open the data file ({error}). Starting with an empty list.",
        "warn_invalid_json": "The data file is not valid JSON ({error}). TaskMate started with an empty task list.{backup_note}",
        "warn_bad_structure": "The data file has an unexpected structure. TaskMate started with an empty task list.{backup_note}",
        "warn_backup_note": "\n\nThe damaged file was saved as:\n{path}",
        "warn_skipped_tasks": "{count} saved task(s) were invalid and were not loaded.\n\nA copy of your original file was saved as:\n{path}",
    },
    "ar": {
        # Window and header
        "app_name": "TaskMate",
        "app_subtitle": "مدير المهام الدراسية",
        "language_label": "اللغة",

        # Dashboard cards
        "stat_total": "إجمالي المهام",
        "stat_pending": "قيد التنفيذ",
        "stat_completed": "مكتملة",
        "stat_overdue": "متأخرة",

        # Toolbar
        "search": "بحث",
        "status": "الحالة",
        "priority": "الأولوية",
        "all": "الكل",
        "clear_filters": "مسح الفلاتر",
        "sort_due_date": "تاريخ التسليم",

        # Table headings
        "col_title": "العنوان",
        "col_subject": "المادة",
        "col_due": "تاريخ التسليم",
        "col_priority": "الأولوية",
        "col_status": "الحالة",

        # Priority and status values
        "priority_Low": "منخفضة",
        "priority_Medium": "متوسطة",
        "priority_High": "عالية",
        "status_Pending": "قيد التنفيذ",
        "status_Completed": "مكتملة",

        # Action buttons
        "add_task": "+ إضافة مهمة",
        "edit_task": "تعديل المهمة",
        "mark_complete": "تحديد كمكتملة",
        "mark_pending": "إعادة إلى قيد التنفيذ",
        "delete_task": "حذف المهمة",
        "autosave_note": "يتم حفظ التغييرات تلقائياً.",

        # Add / edit dialog
        "dialog_add_title": "إضافة مهمة جديدة",
        "dialog_edit_title": "تعديل المهمة",
        "field_title": "العنوان *",
        "field_subject": "المادة",
        "field_due": "تاريخ التسليم *",
        "due_hint": "الصيغة: YYYY-MM-DD (مثال: 2026-12-31)",
        "field_priority": "الأولوية",
        "field_status": "الحالة",
        "field_description": "الوصف",
        "save_task": "حفظ المهمة",
        "cancel": "إلغاء",

        # Status bar
        "status_bar": "عرض {shown} من {total} مهمة.   ملف البيانات: {path}",

        # Messages
        "title_no_selection": "لم يتم تحديد مهمة",
        "msg_no_selection": "يرجى تحديد مهمة من القائمة أولاً.",
        "title_invalid_input": "إدخال غير صحيح",
        "title_save_failed": "فشل الحفظ",
        "msg_save_failed": "تعذر على TaskMate حفظ مهامك.\n\n{error}",
        "title_delete": "حذف المهمة",
        "msg_delete_confirm": "هل تريد حذف المهمة '{title}'؟\n\nلا يمكن التراجع عن هذا الإجراء.",
        "title_data_warning": "تنبيه البيانات",

        # Validation errors
        "err_title_empty": "لا يمكن أن يكون عنوان المهمة فارغاً.",
        "err_title_long": "يجب ألا يتجاوز العنوان {max} حرفاً.",
        "err_subject_long": "يجب ألا تتجاوز المادة {max} حرفاً.",
        "err_description_long": "يجب ألا يتجاوز الوصف {max} حرفاً.",
        "err_due_required": "تاريخ التسليم مطلوب (الصيغة YYYY-MM-DD).",
        "err_due_invalid": "'{value}' ليس تاريخ تسليم صحيحاً. استخدم الصيغة YYYY-MM-DD، مثل 2026-12-31.",
        "err_priority": "يجب أن تكون الأولوية منخفضة أو متوسطة أو عالية.",
        "err_status": "يجب أن تكون الحالة قيد التنفيذ أو مكتملة.",
        "err_unknown_field": "حقل مهمة غير معروف: {fields}",
        "err_task_entry_not_object": "عنصر المهمة ليس كائناً صالحاً.",
        "err_task_id": "عنصر المهمة لا يحتوي على معرّف صالح.",

        # Data file warnings
        "warn_open_failed": "تعذر فتح ملف البيانات ({error}). سيتم البدء بقائمة فارغة.",
        "warn_invalid_json": "ملف البيانات ليس بصيغة JSON صالحة ({error}). بدأ TaskMate بقائمة مهام فارغة.{backup_note}",
        "warn_bad_structure": "ملف البيانات بتركيب غير متوقع. بدأ TaskMate بقائمة مهام فارغة.{backup_note}",
        "warn_backup_note": "\n\nتم حفظ الملف التالف باسم:\n{path}",
        "warn_skipped_tasks": "{count} من المهام المحفوظة غير صالحة ولم يتم تحميلها.\n\nتم حفظ نسخة من الملف الأصلي في:\n{path}",
    },
}

_current_language = DEFAULT_LANGUAGE


def set_language(code):
    """Choose the language used by t(). Unknown codes are ignored."""
    global _current_language
    if code in LANGUAGES:
        _current_language = code


def get_language():
    return _current_language


def is_rtl():
    """True when the current language is written right-to-left."""
    return _current_language == "ar"


def t(key, **params):
    """Return the text for key in the current language, filled with params.

    Falls back to English if a translation is missing, and to the key itself
    if the key does not exist at all.
    """
    table = TRANSLATIONS.get(_current_language, {})
    text = table.get(key) or TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
    return text.format(**params) if params else text
