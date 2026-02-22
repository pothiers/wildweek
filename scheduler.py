#!/usr/bin/env python3
import csv
import sys

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def parse_float(value, field, row_num):
    try:
        num = float(value)
    except ValueError:
        raise ValueError(f"row {row_num}: invalid {field} '{value}'")
    if num < 0:
        raise ValueError(f"row {row_num}: {field} must be non-negative")
    return num


def load_tasks(path):
    tasks = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"task", "hours", "daily_limit"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValueError("CSV must include headers: task,hours,daily_limit")
        for i, row in enumerate(reader, start=2):
            name = (row.get("task") or "").strip()
            if not name:
                raise ValueError(f"row {i}: task is required")
            hours = parse_float(row.get("hours", ""), "hours", i)
            daily = parse_float(row.get("daily_limit", ""), "daily_limit", i)
            tasks.append({"task": name, "remaining": hours, "daily_limit": daily})
    return tasks


def build_schedule(tasks, max_week_hours):
    week_remaining = max_week_hours
    schedule = {d: [] for d in DAYS}
    for day in DAYS:
        if week_remaining <= 0:
            break
        for task in tasks:
            if week_remaining <= 0:
                break
            if task["remaining"] <= 0 or task["daily_limit"] <= 0:
                continue
            allotted = min(task["remaining"], task["daily_limit"], week_remaining)
            if allotted > 0:
                schedule[day].append((task["task"], allotted))
                task["remaining"] -= allotted
                week_remaining -= allotted
    return schedule


def print_schedule(schedule):
    for day in DAYS:
        entries = schedule[day]
        if not entries:
            print(f"{day}: -")
            continue
        parts = [f"{name}:{hours:g}" for name, hours in entries]
        print(f"{day}: " + ", ".join(parts))


def main(argv):
    if len(argv) != 3:
        print("Usage: python scheduler.py <tasks.csv> <max_week_hours>")
        return 1
    csv_path = argv[1]
    try:
        max_week_hours = float(argv[2])
        if max_week_hours < 0:
            raise ValueError
    except ValueError:
        print("max_week_hours must be a non-negative number")
        return 1
    try:
        tasks = load_tasks(csv_path)
        schedule = build_schedule(tasks, max_week_hours)
    except Exception as e:
        print(f"Error: {e}")
        return 1
    print_schedule(schedule)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
