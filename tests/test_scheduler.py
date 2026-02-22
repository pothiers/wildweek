import os
import subprocess
import sys
import tempfile
import unittest

import scheduler


class SchedulerTests(unittest.TestCase):
    def test_load_activities(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "a.csv")
            with open(path, "w", encoding="utf-8") as f:
                f.write("name,duration,probability\nWalk,20,0.5\nRead,30,1.0\n")
            rows = scheduler.load_activities(path)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["name"], "Walk")
        self.assertEqual(rows[0]["duration"], 20)
        self.assertEqual(rows[1]["probability"], 1.0)

    def test_schedule_is_deterministic_and_respects_constraints(self):
        activities = [
            {"name": "A", "duration": 10, "probability": 0.6},
            {"name": "B", "duration": 20, "probability": 0.4},
            {"name": "C", "duration": 15, "probability": 0.7},
        ]
        first = scheduler.schedule(activities, days=6, min_minutes=10, max_minutes=35)
        second = scheduler.schedule(activities, days=6, min_minutes=10, max_minutes=35)
        self.assertEqual(first, second)
        for day in first:
            names = [a["name"] for a in day]
            total = sum(a["duration"] for a in day)
            self.assertEqual(len(names), len(set(names)))
            self.assertLessEqual(total, 35)
            self.assertGreaterEqual(total, 10)

    def test_write_ics_creates_valid_calendar_text(self):
        days = [[{"name": "Walk", "duration": 20, "probability": 1.0}], []]
        with tempfile.TemporaryDirectory() as td:
            ics = os.path.join(td, "out.ics")
            scheduler.write_ics(days, ics)
            with open(ics, encoding="utf-8") as f:
                text = f.read()
        self.assertIn("BEGIN:VCALENDAR", text)
        self.assertIn("END:VCALENDAR", text)
        self.assertIn("BEGIN:VEVENT", text)
        self.assertIn("SUMMARY:Walk", text)

    def test_cli_overrides_config(self):
        with tempfile.TemporaryDirectory() as td:
            csv_path = os.path.join(td, "in.csv")
            cfg_path = os.path.join(td, "cfg.conf")
            cli_ics = os.path.join(td, "cli.ics")
            cfg_ics = os.path.join(td, "cfg.ics")
            with open(csv_path, "w", encoding="utf-8") as f:
                f.write("name,duration,probability\nLong,30,1.0\n")
            with open(cfg_path, "w", encoding="utf-8") as f:
                f.write(f"csv={csv_path}\nmin_minutes=0\nmax_minutes=60\ndays=1\nics_file={cfg_ics}\n")
            cp = subprocess.run(
                [
                    sys.executable,
                    "scheduler.py",
                    "--config",
                    cfg_path,
                    "--max_minutes",
                    "25",
                    "--ics_file",
                    cli_ics,
                ],
                cwd=os.getcwd(),
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("1 (Mon) | 0 | -", cp.stdout)
            self.assertTrue(os.path.exists(cli_ics))
            self.assertFalse(os.path.exists(cfg_ics))


if __name__ == "__main__":
    unittest.main()
