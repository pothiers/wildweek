#!/usr/bin/env python3
import csv
import sys
import argparse
import configparser
import os
import random
from datetime import date, timedelta

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def load_tasks(csv_path):
    tasks = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"].strip()
            if not name:
                continue
            duration = int(row["duration"])
            probability = float(row["probability"]) if "probability" in row else 1.0
            tasks.append({"name": name, "duration": duration, "probability": probability})
    return tasks


def schedule(tasks, daily_limit, max_week_minutes, seed):
    rng = random.Random(seed)
    week = {day: [] for day in DAYS}
    week_total = 0

    for day in DAYS:
        day_total = 0
        for task in tasks:
            if week_total + task["duration"] > max_week_minutes:
                break
            if rng.random() >= task["probability"]:
                continue
            if day_total + task["duration"] > daily_limit:
                continue
            week[day].append(task)
            day_total += task["duration"]
            week_total += task["duration"]

    return week


def print_schedule(week, label):
    print(f"\n{label}")
    for day in DAYS:
        tasks = week[day]
        if tasks:
            items = ", ".join(f"{t['name']} ({t['duration']}min)" for t in tasks)
        else:
            items = "(rest)"
        print(f"  {day}: {items}")


def write_ics(weeks, filename):
    today = date.today()
    days_until_monday = (7 - today.weekday()) % 7
    first_monday = today + timedelta(days=days_until_monday if days_until_monday else 7)

    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Wildweek//EN"]
    for w, week in enumerate(weeks):
        week_start = first_monday + timedelta(weeks=w)
        for i, day in enumerate(DAYS):
            day_date = week_start + timedelta(days=i)
            for task in week[day]:
                uid = f"{day_date.strftime('%Y%m%d')}-{task['name'].replace(' ', '')}@wildweek"
                lines += [
                    "BEGIN:VEVENT",
                    f"UID:{uid}",
                    f"DTSTART;VALUE=DATE:{day_date.strftime('%Y%m%d')}",
                    f"DTEND;VALUE=DATE:{(day_date + timedelta(days=1)).strftime('%Y%m%d')}",
                    f"SUMMARY:{task['name']} ({task['duration']}min)",
                    "END:VEVENT",
                ]
    lines.append("END:VCALENDAR")
    with open(filename, "w") as f:
        f.write("\r\n".join(lines) + "\r\n")
    print(f"ICS written to {filename}")


def load_config(path="wildweek.cfg"):
    config = {"csv": None, "daily_limit": 120, "max_week_minutes": 600, "seed": 42, "ics": None, "weeks": 3}
    if os.path.exists(path):
        cp = configparser.ConfigParser()
        cp.read(path)
        sec = cp["wildweek"] if "wildweek" in cp else {}
        if "csv" in sec:
            config["csv"] = sec["csv"]
        if "daily_limit" in sec:
            config["daily_limit"] = int(sec["daily_limit"])
        if "max_week_minutes" in sec:
            config["max_week_minutes"] = int(sec["max_week_minutes"])
        if "seed" in sec:
            config["seed"] = int(sec["seed"])
        if "ics" in sec:
            config["ics"] = sec["ics"]
        if "weeks" in sec:
            config["weeks"] = int(sec["weeks"])
    return config


def main():
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--config", default="wildweek.cfg")
    pre_args, _ = pre.parse_known_args()
    config = load_config(pre_args.config)

    parser = argparse.ArgumentParser(description="Deterministic weekly scheduler")
    parser.add_argument("--config", default="wildweek.cfg",
                        help="Path to config file (default: wildweek.cfg)")
    parser.add_argument("csv", nargs="?", default=config["csv"],
                        help="Path to tasks CSV file")
    parser.add_argument("--daily-limit", type=int, default=config["daily_limit"],
                        help="Max minutes per day")
    parser.add_argument("--max-week-minutes", type=int, default=config["max_week_minutes"],
                        help="Max minutes per week")
    parser.add_argument("--seed", type=int, default=config["seed"],
                        help="Random seed for task selection")
    parser.add_argument("--ics", default=config["ics"],
                        help="Output ICS filename (optional)")
    parser.add_argument("--weeks", type=int, default=config["weeks"],
                        help="Number of weeks to generate (default: 3)")
    args = parser.parse_args()

    if not args.csv:
        parser.error("csv is required (via argument or wildweek.cfg)")

    tasks = load_tasks(args.csv)
    weeks = []
    for i in range(args.weeks):
        week = schedule(tasks, args.daily_limit, args.max_week_minutes, args.seed + i)
        weeks.append(week)
        print_schedule(week, f"Week {i + 1}")
    if args.ics:
        write_ics(weeks, args.ics)


if __name__ == "__main__":
    main()
