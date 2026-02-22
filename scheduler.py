#!/usr/bin/env python3
import csv
import sys

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def parse_int(name, value):
    try:
        n = int(value)
    except ValueError:
        raise SystemExit(f"Invalid {name}: {value}")
    if n < 0:
        raise SystemExit(f"{name} must be >= 0")
    return n


def read_tasks(path):
    tasks = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            task = (row.get("task") or "").strip()
            hrs = (row.get("hours") or "").strip()
            if not task or not hrs:
                raise SystemExit("CSV must have task,hours columns with values")
            tasks.append([task, parse_int("hours", hrs)])
    if not tasks:
        raise SystemExit("CSV has no tasks")
    return tasks


def schedule(tasks, daily_limit, max_week_hours):
    week = {d: [] for d in DAYS}
    day_used = {d: 0 for d in DAYS}
    week_used = 0
    day_i = 0
    for task, need in tasks:
        while need > 0 and week_used < max_week_hours and day_i < len(DAYS):
            day = DAYS[day_i]
            day_cap = daily_limit - day_used[day]
            week_cap = max_week_hours - week_used
            if day_cap <= 0:
                day_i += 1
                continue
            take = min(need, day_cap, week_cap)
            if take <= 0:
                break
            week[day].append((task, take))
            day_used[day] += take
            week_used += take
            need -= take
            if day_used[day] >= daily_limit:
                day_i += 1
    return week, week_used


def print_schedule(week, week_used):
    print(f"Total scheduled hours: {week_used}")
    for day in DAYS:
        items = week[day]
        if not items:
            print(f"{day}: -")
            continue
        parts = [f"{task}:{hours}" for task, hours in items]
        print(f"{day}: " + ", ".join(parts))


def main(argv):
    if len(argv) != 4:
        raise SystemExit("Usage: python scheduler.py <tasks.csv> <daily_limit> <max_week_hours>")
    csv_path = argv[1]
    daily_limit = parse_int("daily_limit", argv[2])
    max_week_hours = parse_int("max_week_hours", argv[3])
    tasks = read_tasks(csv_path)
    week, week_used = schedule(tasks, daily_limit, max_week_hours)
    print_schedule(week, week_used)


if __name__ == "__main__":
    main(sys.argv)
