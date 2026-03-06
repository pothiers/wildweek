#!/usr/bin/env python3
import csv
import sys
import argparse
import configparser
import os
import random

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def load_tasks(csv_path):
    tasks = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"].strip()
            duration = int(row["duration"])
            probability = float(row["probability"]) if "probability" in row else 1.0
            if name:
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


def print_schedule(week):
    for day in DAYS:
        tasks = week[day]
        if tasks:
            items = ", ".join(f"{t['name']} ({t['duration']}min)" for t in tasks)
        else:
            items = "(rest)"
        print(f"{day}: {items}")


def load_config(path="wildweek.cfg"):
    config = {"csv": None, "daily_limit": 120, "max_week_minutes": 600, "seed": 42}
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
    return config


def main():
    config = load_config()

    parser = argparse.ArgumentParser(description="Deterministic weekly scheduler")
    parser.add_argument("csv", nargs="?", default=config["csv"],
                        help="Path to tasks CSV file")
    parser.add_argument("--daily-limit", type=int, default=config["daily_limit"],
                        help="Max minutes per day")
    parser.add_argument("--max-week-minutes", type=int, default=config["max_week_minutes"],
                        help="Max minutes per week")
    parser.add_argument("--seed", type=int, default=config["seed"],
                        help="Random seed for task selection")
    args = parser.parse_args()

    if not args.csv:
        parser.error("csv is required (via argument or wildweek.cfg)")

    tasks = load_tasks(args.csv)
    week = schedule(tasks, args.daily_limit, args.max_week_minutes, args.seed)
    print_schedule(week)


if __name__ == "__main__":
    main()
