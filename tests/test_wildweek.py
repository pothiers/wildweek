#!/usr/bin/env python3
import unittest
import tempfile
import os
from wildweek import load_tasks, schedule, write_ics, load_config, DAYS


TASKS = [
    {"name": "Alpha", "duration": 30, "probability": 1.0},
    {"name": "Beta",  "duration": 20, "probability": 1.0},
    {"name": "Gamma", "duration": 60, "probability": 0.0},  # never selected
]


class TestLoadTasks(unittest.TestCase):
    def test_loads_all_columns(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("name,duration,probability\nHike,90,0.4\nWalk,30,0.8\n")
            path = f.name
        try:
            tasks = load_tasks(path)
            self.assertEqual(len(tasks), 2)
            self.assertEqual(tasks[0], {"name": "Hike", "duration": 90, "probability": 0.4})
        finally:
            os.unlink(path)

    def test_missing_probability_defaults_to_1(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("name,duration\nTask,10\n")
            path = f.name
        try:
            tasks = load_tasks(path)
            self.assertEqual(tasks[0]["probability"], 1.0)
        finally:
            os.unlink(path)

    def test_skips_blank_rows(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("name,duration,probability\nHike,90,0.4\n,,,\n")
            path = f.name
        try:
            tasks = load_tasks(path)
            self.assertEqual(len(tasks), 1)
        finally:
            os.unlink(path)


class TestSchedule(unittest.TestCase):
    def test_deterministic_same_seed(self):
        w1 = schedule(TASKS, 120, 600, 42)
        w2 = schedule(TASKS, 120, 600, 42)
        self.assertEqual(w1, w2)

    def test_different_seeds_differ(self):
        tasks = [{"name": f"T{i}", "duration": 10, "probability": 0.5} for i in range(10)]
        w1 = schedule(tasks, 120, 600, 1)
        w2 = schedule(tasks, 120, 600, 2)
        self.assertNotEqual(w1, w2)

    def test_probability_zero_never_scheduled(self):
        week = schedule(TASKS, 120, 600, 42)
        for day in DAYS:
            names = [t["name"] for t in week[day]]
            self.assertNotIn("Gamma", names)

    def test_probability_one_always_scheduled(self):
        tasks = [{"name": "Sure", "duration": 10, "probability": 1.0}]
        week = schedule(tasks, 120, 600, 42)
        for day in DAYS:
            self.assertEqual(len(week[day]), 1)

    def test_daily_limit_respected(self):
        week = schedule(TASKS, 40, 9999, 42)
        for day in DAYS:
            total = sum(t["duration"] for t in week[day])
            self.assertLessEqual(total, 40)

    def test_max_week_minutes_respected(self):
        tasks = [{"name": "T", "duration": 10, "probability": 1.0}]
        week = schedule(tasks, 120, 50, 42)
        total = sum(t["duration"] for day in DAYS for t in week[day])
        self.assertLessEqual(total, 50)

    def test_seven_days(self):
        week = schedule(TASKS, 120, 600, 42)
        self.assertEqual(list(week.keys()), DAYS)


class TestWriteIcs(unittest.TestCase):
    def test_ics_structure(self):
        week = schedule(TASKS, 120, 600, 42)
        with tempfile.NamedTemporaryFile(suffix=".ics", delete=False) as f:
            path = f.name
        try:
            write_ics([week], path)
            with open(path) as fh:
                content = fh.read()
            self.assertIn("BEGIN:VCALENDAR", content)
            self.assertIn("END:VCALENDAR", content)
            self.assertIn("BEGIN:VEVENT", content)
        finally:
            os.unlink(path)

    def test_ics_event_count_matches_scheduled_tasks(self):
        week = schedule(TASKS, 120, 600, 42)
        total_tasks = sum(len(week[day]) for day in DAYS)
        with tempfile.NamedTemporaryFile(suffix=".ics", delete=False) as f:
            path = f.name
        try:
            write_ics([week], path)
            with open(path) as fh:
                content = fh.read()
            self.assertEqual(content.count("BEGIN:VEVENT"), total_tasks)
        finally:
            os.unlink(path)

    def test_multi_week_ics_event_count(self):
        weeks = [schedule(TASKS, 120, 600, 42 + i) for i in range(3)]
        total_tasks = sum(len(week[day]) for week in weeks for day in DAYS)
        with tempfile.NamedTemporaryFile(suffix=".ics", delete=False) as f:
            path = f.name
        try:
            write_ics(weeks, path)
            with open(path) as fh:
                content = fh.read()
            self.assertEqual(content.count("BEGIN:VEVENT"), total_tasks)
        finally:
            os.unlink(path)


class TestLoadConfig(unittest.TestCase):
    def test_defaults_without_file(self):
        config = load_config("/nonexistent/path.cfg")
        self.assertEqual(config["daily_limit"], 120)
        self.assertEqual(config["max_week_minutes"], 600)
        self.assertEqual(config["seed"], 42)
        self.assertEqual(config["weeks"], 3)
        self.assertEqual(config["ics"], "wildweek.ics")

    def test_reads_values_from_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cfg", delete=False) as f:
            f.write("[wildweek]\ndaily_limit = 90\nseed = 7\nweeks = 2\n")
            path = f.name
        try:
            config = load_config(path)
            self.assertEqual(config["daily_limit"], 90)
            self.assertEqual(config["seed"], 7)
            self.assertEqual(config["weeks"], 2)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
