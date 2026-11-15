"""
Unit tests for TaskMate's core logic and JSON storage.

Run from the project folder with:
    python -m unittest discover -s tests -v

These tests do not open any window, so they also run without a display.
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import date

# Make the project modules importable when running from the tests folder
PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_FOLDER)

import storage  # noqa: E402
from task_manager import Task, TaskManager, TaskValidationError  # noqa: E402

TODAY = date(2026, 11, 15)


class TaskManagerTests(unittest.TestCase):

    def setUp(self):
        self.manager = TaskManager()

    def add_sample(self, title="Math homework", due="2026-11-20", priority="Medium",
                   subject="Math", status="Pending"):
        return self.manager.add_task(title=title, description="desc", subject=subject,
                                     due_date=due, priority=priority, status=status)

    # Adding
    def test_add_task_creates_task_with_all_fields(self):
        task = self.add_sample(priority="High")
        self.assertEqual(task.task_id, 1)
        self.assertEqual(task.title, "Math homework")
        self.assertEqual(task.subject, "Math")
        self.assertEqual(task.priority, "High")
        self.assertEqual(task.status, "Pending")
        self.assertEqual(len(self.manager.tasks), 1)

    def test_add_task_rejects_empty_title(self):
        for empty_title in ("", "   ", None):
            with self.assertRaises(TaskValidationError):
                self.manager.add_task(title=empty_title, due_date="2026-12-01")
        self.assertEqual(self.manager.tasks, [])

    def test_add_task_rejects_bad_dates(self):
        for bad_date in ("", "2026/12/01", "01-12-2026", "2026-02-30", "tomorrow"):
            with self.assertRaises(TaskValidationError, msg=bad_date):
                self.manager.add_task(title="X", due_date=bad_date)

    def test_add_task_rejects_invalid_priority_and_status(self):
        with self.assertRaises(TaskValidationError):
            self.manager.add_task(title="X", due_date="2026-12-01", priority="Urgent")
        with self.assertRaises(TaskValidationError):
            self.manager.add_task(title="X", due_date="2026-12-01", status="Done")

    def test_add_task_rejects_too_long_title(self):
        with self.assertRaises(TaskValidationError):
            self.manager.add_task(title="a" * 101, due_date="2026-12-01")

    def test_ids_are_unique_and_increase(self):
        first = self.add_sample()
        second = self.add_sample(title="Essay")
        self.assertEqual(second.task_id, first.task_id + 1)

    # Editing
    def test_edit_task_updates_fields(self):
        task = self.add_sample()
        self.manager.edit_task(task.task_id, title="Algebra", priority="High")
        self.assertEqual(task.title, "Algebra")
        self.assertEqual(task.priority, "High")
        self.assertEqual(task.subject, "Math")  # unchanged

    def test_edit_task_invalid_change_leaves_task_unchanged(self):
        task = self.add_sample()
        with self.assertRaises(TaskValidationError):
            self.manager.edit_task(task.task_id, title="", due_date="2026-13-40")
        self.assertEqual(task.title, "Math homework")
        self.assertEqual(task.due_date, "2026-11-20")

    def test_edit_unknown_task_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.manager.edit_task(999, title="Nope")

    def test_edit_unknown_field_is_rejected(self):
        task = self.add_sample()
        with self.assertRaises(TaskValidationError):
            self.manager.edit_task(task.task_id, colour="red")

    # Deleting
    def test_delete_task_removes_it(self):
        task = self.add_sample()
        self.manager.delete_task(task.task_id)
        self.assertIsNone(self.manager.find_task(task.task_id))
        self.assertEqual(self.manager.tasks, [])

    def test_delete_unknown_task_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.manager.delete_task(42)

    # Completing
    def test_complete_task_and_reopen(self):
        task = self.add_sample()
        self.manager.complete_task(task.task_id)
        self.assertEqual(task.status, "Completed")
        self.manager.complete_task(task.task_id, completed=False)
        self.assertEqual(task.status, "Pending")

    # Dashboard
    def test_statistics(self):
        self.add_sample(title="Old pending", due="2026-11-01")                # overdue
        self.add_sample(title="Old done", due="2026-11-01", status="Completed")  # not overdue
        self.add_sample(title="Future", due="2026-12-01")
        stats = self.manager.get_statistics(today=TODAY)
        self.assertEqual(stats, {"total": 3, "pending": 2, "completed": 1, "overdue": 1})

    def test_due_today_is_not_overdue(self):
        task = self.add_sample(due="2026-11-15")
        self.assertFalse(task.is_overdue(TODAY))

    # Filtering, searching, sorting
    def test_filter_by_status_and_priority(self):
        self.add_sample(title="A", priority="High", status="Completed")
        self.add_sample(title="B", priority="Low")
        self.add_sample(title="C", priority="High")
        titles = [t.title for t in self.manager.show_tasks(status_filter="Pending", priority_filter="High")]
        self.assertEqual(titles, ["C"])
        self.assertEqual(len(self.manager.show_tasks(status_filter="Completed")), 1)
        self.assertEqual(len(self.manager.show_tasks()), 3)

    def test_search_by_title_or_subject_case_insensitive(self):
        self.add_sample(title="Read chapter 4", subject="History")
        self.add_sample(title="Lab report", subject="Physics")
        self.assertEqual([t.title for t in self.manager.show_tasks(search_text="chapter")],
                         ["Read chapter 4"])
        self.assertEqual([t.title for t in self.manager.show_tasks(search_text="PHYS")],
                         ["Lab report"])
        self.assertEqual(self.manager.show_tasks(search_text="zzz"), [])

    def test_sort_by_due_date_ascending_and_descending(self):
        self.add_sample(title="Third", due="2026-12-03")
        self.add_sample(title="First", due="2026-11-01")
        self.add_sample(title="Second", due="2026-11-20")
        asc = [t.title for t in self.manager.show_tasks(sort_ascending=True)]
        desc = [t.title for t in self.manager.show_tasks(sort_ascending=False)]
        self.assertEqual(asc, ["First", "Second", "Third"])
        self.assertEqual(desc, ["Third", "Second", "First"])

    def test_same_due_date_sorts_high_priority_first(self):
        self.add_sample(title="Low one", due="2026-11-20", priority="Low")
        self.add_sample(title="High one", due="2026-11-20", priority="High")
        titles = [t.title for t in self.manager.show_tasks()]
        self.assertEqual(titles, ["High one", "Low one"])

    def test_loaded_duplicate_ids_are_fixed(self):
        first = Task(5, "A", "", "", "2026-12-01", "Low", "Pending")
        second = Task(5, "B", "", "", "2026-12-01", "Low", "Pending")
        TaskManager([first, second])
        self.assertNotEqual(first.task_id, second.task_id)


class StorageTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = os.path.join(self.temp_dir.name, "tasks.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_missing_file_gives_empty_list_without_warning(self):
        tasks, warning = storage.load_tasks(self.data_file)
        self.assertEqual(tasks, [])
        self.assertIsNone(warning)

    def test_save_then_load_round_trip(self):
        manager = TaskManager()
        manager.add_task(title="Essay", description="Two pages", subject="English",
                         due_date="2026-12-01", priority="High")
        manager.add_task(title="Quiz", due_date="2026-11-30", status="Completed")
        storage.save_tasks(manager.tasks, self.data_file)

        loaded, warning = storage.load_tasks(self.data_file)
        self.assertIsNone(warning)
        self.assertEqual([t.to_dict() for t in loaded], [t.to_dict() for t in manager.tasks])

    def test_saved_file_is_valid_json_with_version(self):
        manager = TaskManager()
        manager.add_task(title="Essay", due_date="2026-12-01")
        storage.save_tasks(manager.tasks, self.data_file)
        with open(self.data_file, encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertEqual(data["version"], 1)
        self.assertEqual(data["tasks"][0]["title"], "Essay")

    def test_unicode_titles_survive_round_trip(self):
        manager = TaskManager()
        manager.add_task(title="الواجب الأول", subject="عربي", due_date="2026-12-01")
        storage.save_tasks(manager.tasks, self.data_file)
        loaded, _ = storage.load_tasks(self.data_file)
        self.assertEqual(loaded[0].title, "الواجب الأول")

    def test_corrupted_json_is_backed_up_and_does_not_crash(self):
        with open(self.data_file, "w", encoding="utf-8") as handle:
            handle.write("{this is not json")
        tasks, warning = storage.load_tasks(self.data_file)
        self.assertEqual(tasks, [])
        self.assertIsNotNone(warning)
        self.assertFalse(os.path.exists(self.data_file))
        backups = [name for name in os.listdir(self.temp_dir.name) if ".corrupt-" in name]
        self.assertEqual(len(backups), 1)

    def test_wrong_structure_is_handled(self):
        with open(self.data_file, "w", encoding="utf-8") as handle:
            json.dump({"tasks": "not a list"}, handle)
        tasks, warning = storage.load_tasks(self.data_file)
        self.assertEqual(tasks, [])
        self.assertIsNotNone(warning)

    def test_invalid_entries_are_skipped_but_valid_ones_kept(self):
        good = {"id": 1, "title": "Good", "description": "", "subject": "",
                "due_date": "2026-12-01", "priority": "Low", "status": "Pending"}
        bad_title = dict(good, id=2, title="   ")
        bad_date = dict(good, id=3, due_date="not-a-date")
        with open(self.data_file, "w", encoding="utf-8") as handle:
            json.dump({"version": 1, "tasks": [good, bad_title, bad_date, "text"]}, handle)
        tasks, warning = storage.load_tasks(self.data_file)
        self.assertEqual([t.title for t in tasks], ["Good"])
        self.assertIn("3 saved task(s)", warning)

    def test_empty_file_is_treated_as_no_tasks(self):
        open(self.data_file, "w", encoding="utf-8").close()
        tasks, warning = storage.load_tasks(self.data_file)
        self.assertEqual(tasks, [])
        self.assertIsNone(warning)

    def test_no_temporary_files_left_after_save(self):
        storage.save_tasks([], self.data_file)
        self.assertEqual(os.listdir(self.temp_dir.name), ["tasks.json"])


if __name__ == "__main__":
    unittest.main()
