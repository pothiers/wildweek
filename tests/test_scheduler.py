import os
import random
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

    def test_schedule_same_seed_same_output(self):
        activities = [
            {"name": "A", "duration": 20, "probability": 1.0},
            {"name": "B", "duration": 20, "probability": 1.0},
            {"name": "C", "duration": 20, "probability": 1.0},
            {"name": "D", "duration": 20, "probability": 1.0},
        ]
        first = scheduler.schedule(activities, days=5, min_minutes=0, max_minutes=40, rng=random.Random("99"))
        second = scheduler.schedule(activities, days=5, min_minutes=0, max_minutes=40, rng=random.Random("99"))
        self.assertEqual(first, second)

    def test_schedule_different_seed_can_change_output(self):
        activities = [
            {"name": "A", "duration": 20, "probability": 1.0},
            {"name": "B", "duration": 20, "probability": 1.0},
            {"name": "C", "duration": 20, "probability": 1.0},
            {"name": "D", "duration": 20, "probability": 1.0},
        ]
        first = scheduler.schedule(activities, days=5, min_minutes=0, max_minutes=40, rng=random.Random("99"))
        second = scheduler.schedule(activities, days=5, min_minutes=0, max_minutes=40, rng=random.Random("100"))
        self.assertNotEqual(first, second)

    def test_days_cannot_exceed_five_weeks(self):
        activities = [{"name": "A", "duration": 20, "probability": 1.0}]
        with self.assertRaises(SystemExit):
            scheduler.schedule(activities, days=36, min_minutes=0, max_minutes=40)

    def test_days_35_is_allowed(self):
        activities = [{"name": "A", "duration": 20, "probability": 1.0}]
        out = scheduler.schedule(activities, days=35, min_minutes=0, max_minutes=40)
        self.assertEqual(len(out), 35)

    def test_write_schedule_ics_creates_valid_ics_text(self):
        days = [[{"name": "Walk", "duration": 20, "probability": 1.0}], []]
        with tempfile.TemporaryDirectory() as td:
            out_ics = os.path.join(td, "out.ics")
            scheduler.write_schedule_ics(days, out_ics)
            with open(out_ics, encoding="utf-8") as f:
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
            cli_csv = os.path.join(td, "cli.csv")
            cfg_csv = os.path.join(td, "cfg.csv")
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
            self.assertTrue(os.path.exists(cli_csv))
            self.assertFalse(os.path.exists(cfg_ics))
            self.assertFalse(os.path.exists(cfg_csv))

    def test_csv_output_is_written_alongside_ics(self):
        with tempfile.TemporaryDirectory() as td:
            days = [[{"name": "Walk", "duration": 20, "probability": 1.0}, {"name": "Read", "duration": 10, "probability": 1.0}], []]
            out_ics = os.path.join(td, "out.ics")
            out_csv = os.path.join(td, "out.csv")
            scheduler.write_schedule_ics(days, out_ics)
            scheduler.write_schedule_csv(days, out_csv)
            with open(out_csv, encoding="utf-8") as f:
                text = f.read()
            self.assertTrue(os.path.exists(out_ics))
            self.assertIn("day,date,weekday,activity,duration,start_time,end_time", text)
            self.assertIn(",Walk,20,09:00,09:20", text)
            self.assertIn(",Read,10,09:30,09:40", text)

    def test_csv_filename_is_derived_from_ics_filename(self):
        self.assertEqual(scheduler.csv_from_ics_filename("wildweeks.ics"), "wildweeks.csv")
        self.assertEqual(scheduler.csv_from_ics_filename("custom-name"), "custom-name.csv")

    def test_cli_rejects_more_than_35_days(self):
        with tempfile.TemporaryDirectory() as td:
            csv_path = os.path.join(td, "in.csv")
            out_csv = os.path.join(td, "out.ics")
            with open(csv_path, "w", encoding="utf-8") as f:
                f.write("name,duration,probability\nLong,30,1.0\n")
            cp = subprocess.run(
                [
                    sys.executable,
                    "scheduler.py",
                    "--csv",
                    csv_path,
                    "--days",
                    "36",
                    "--ics_file",
                    out_csv,
                ],
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(cp.returncode, 0)
            self.assertIn("days must be <= 35 (5 weeks)", cp.stderr)

    def test_cli_uses_weeks_from_config_when_days_missing(self):
        with tempfile.TemporaryDirectory() as td:
            csv_path = os.path.join(td, "in.csv")
            cfg_path = os.path.join(td, "cfg.conf")
            out_csv = os.path.join(td, "out.ics")
            with open(csv_path, "w", encoding="utf-8") as f:
                f.write("name,duration,probability\nQuiet,10,1.0\n")
            with open(cfg_path, "w", encoding="utf-8") as f:
                f.write(
                    f"csv={csv_path}\nmin_minutes=0\nmax_minutes=60\nweeks=2\nics_file={out_csv}\n"
                )
            subprocess.run(
                [sys.executable, "scheduler.py", "--config", cfg_path],
                cwd=os.getcwd(),
                check=True,
                capture_output=True,
                text=True,
            )
            with open(out_csv, encoding="utf-8") as f:
                text = f.read()
            self.assertEqual(text.count("BEGIN:VEVENT"), 14)

    def test_cli_uses_days_from_config_over_weeks(self):
        with tempfile.TemporaryDirectory() as td:
            csv_path = os.path.join(td, "in.csv")
            cfg_path = os.path.join(td, "cfg.conf")
            out_csv = os.path.join(td, "out.ics")
            with open(csv_path, "w", encoding="utf-8") as f:
                f.write("name,duration,probability\nQuiet,10,1.0\n")
            with open(cfg_path, "w", encoding="utf-8") as f:
                f.write(
                    f"csv={csv_path}\nmin_minutes=0\nmax_minutes=60\nweeks=2\ndays=3\nics_file={out_csv}\n"
                )
            subprocess.run(
                [sys.executable, "scheduler.py", "--config", cfg_path],
                cwd=os.getcwd(),
                check=True,
                capture_output=True,
                text=True,
            )
            with open(out_csv, encoding="utf-8") as f:
                text = f.read()
            self.assertEqual(text.count("BEGIN:VEVENT"), 3)

    def test_cli_days_overrides_config_days_and_weeks(self):
        with tempfile.TemporaryDirectory() as td:
            csv_path = os.path.join(td, "in.csv")
            cfg_path = os.path.join(td, "cfg.conf")
            out_csv = os.path.join(td, "out.ics")
            with open(csv_path, "w", encoding="utf-8") as f:
                f.write("name,duration,probability\nQuiet,10,1.0\n")
            with open(cfg_path, "w", encoding="utf-8") as f:
                f.write(
                    f"csv={csv_path}\nmin_minutes=0\nmax_minutes=60\nweeks=2\ndays=3\nics_file={out_csv}\n"
                )
            subprocess.run(
                [sys.executable, "scheduler.py", "--config", cfg_path, "--days", "5"],
                cwd=os.getcwd(),
                check=True,
                capture_output=True,
                text=True,
            )
            with open(out_csv, encoding="utf-8") as f:
                text = f.read()
            self.assertEqual(text.count("BEGIN:VEVENT"), 5)


if __name__ == "__main__":
    unittest.main()
