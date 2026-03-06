#!/usr/bin/env python3
import csv
import sys
import argparse

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def load_tasks(csv_path):
    tasks = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"].strip()
            duration = int(row["duration"])
            if name:
                tasks.append({"name": name, "duration": duration})
    return tasks


def schedule(tasks, daily_limit, max_week_minutes):
    week = {day: [] for day in DAYS}
    week_total = 0

    for day in DAYS:
        day_total = 0
        for task in tasks:
            if week_total + task["duration"] > max_week_minutes:
                break
            if day_total + task["duration"] > daily_limit:
                continue
            week[day].append(task)
            day_total += task["duration"]
            week_total += task["duration"]

    return week


def print_schedule(week):
    for day in DAYS:
        tasks = week[day]
        if tasks:
            items = ", ".join(f"{t['name']} ({t['duration']}min)" for t in tasks)
        else:
            items = "(rest)"
        print(f"{day}: {items}")


def main():
    parser = argparse.ArgumentParser(description="Deterministic weekly scheduler")
    parser.add_argument("csv", help="Path to tasks CSV file")
    parser.add_argument("--daily-limit", type=int, default=120,
                        help="Max minutes per day (default: 120)")
    parser.add_argument("--max-week-minutes", type=int, default=600,
                        help="Max minutes per week (default: 600)")
    args = parser.parse_args()

    tasks = load_tasks(args.csv)
    week = schedule(tasks, args.daily_limit, args.max_week_minutes)
    print_schedule(week)


if __name__ == "__main__":
    main()
