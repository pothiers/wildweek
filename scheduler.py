#!/usr/bin/env python3
import argparse
import csv
import datetime as dt

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def parse_config(path):
    cfg = {}
    if not path:
        return cfg
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith("#") or "=" not in s:
                    continue
                k, v = s.split("=", 1)
                cfg[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return cfg


def as_int(name, value):
    try:
        n = int(value)
    except ValueError:
        raise SystemExit(f"Invalid {name}: {value}")
    if n < 0:
        raise SystemExit(f"{name} must be >= 0")
    return n


def as_float(name, value):
    try:
        n = float(value)
    except ValueError:
        raise SystemExit(f"Invalid {name}: {value}")
    if n < 0 or n > 1:
        raise SystemExit(f"{name} must be in [0,1]")
    return n


def load_activities(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            name = (r.get("name") or "").strip()
            if not name:
                raise SystemExit("CSV requires non-empty name")
            rows.append({
                "name": name,
                "duration": as_int("duration", (r.get("duration") or "").strip()),
                "probability": as_float("probability", (r.get("probability") or "").strip()),
            })
    if not rows:
        raise SystemExit("CSV has no activities")
    return rows


def stable_draw(name, day_idx, draw_idx):
    code = sum((i + 1) * ord(c) for i, c in enumerate(name))
    return ((code + 97 * day_idx + 53 * draw_idx) % 1000) / 1000.0


def schedule(activities, days, min_minutes, max_minutes):
    if min_minutes > max_minutes:
        raise SystemExit("min_minutes must be <= max_minutes")
    last_used = {a["name"]: -10**9 for a in activities}
    out = []
    for d in range(days):
        picked, total = [], 0
        for draw_idx, a in enumerate(activities):
            if total >= max_minutes:
                break
            gap = d - last_used[a["name"]]
            adj_prob = min(1.0, a["probability"] * (1.0 + 0.2 * max(0, gap - 1)))
            if stable_draw(a["name"], d, draw_idx) < adj_prob and total + a["duration"] <= max_minutes:
                picked.append(a)
                total += a["duration"]
        if total < min_minutes:
            remaining = sorted(
                [a for a in activities if a not in picked],
                key=lambda a: min(1.0, a["probability"] * (1.0 + 0.2 * max(0, d - last_used[a["name"]] - 1))),
                reverse=True,
            )
            for a in remaining:
                if total >= min_minutes:
                    break
                if total + a["duration"] <= max_minutes:
                    picked.append(a)
                    total += a["duration"]
        for a in picked:
            last_used[a["name"]] = d
        out.append(picked)
    return out


def print_table(days):
    print("Day | Total Minutes | Activities")
    print("--- | ------------- | ----------")
    for i, activities in enumerate(days, start=1):
        total = sum(a["duration"] for a in activities)
        names = ", ".join(f'{a["name"]}({a["duration"]})' for a in activities) if activities else "-"
        print(f"{i} ({WEEKDAYS[(i - 1) % 7]}) | {total} | {names}")


def write_ics(days, filename):
    start = dt.date.today()
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Wildweek//Scheduler//EN"]
    for i, activities in enumerate(days):
        day = start + dt.timedelta(days=i)
        start_minute = 9 * 60
        for a in activities:
            h, m = divmod(start_minute, 60)
            st = dt.datetime(day.year, day.month, day.day, h, m)
            en = st + dt.timedelta(minutes=a["duration"])
            uid = f"{day.isoformat()}-{a['name'].replace(' ', '_')}-{start_minute}@wildweek"
            lines += [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{stamp}",
                f"SUMMARY:{a['name']}",
                f"DTSTART:{st.strftime('%Y%m%dT%H%M%S')}",
                f"DTEND:{en.strftime('%Y%m%dT%H%M%S')}",
                "END:VEVENT",
            ]
            start_minute += a["duration"]
    lines.append("END:VCALENDAR")
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="wildweek.conf")
    p.add_argument("--csv")
    p.add_argument("--min_minutes", type=int)
    p.add_argument("--max_minutes", type=int)
    p.add_argument("--days", type=int)
    p.add_argument("--ics_file")
    args = p.parse_args()
    cfg = parse_config(args.config)
    csv_path = args.csv or cfg.get("csv")
    if not csv_path:
        raise SystemExit("Missing csv path (use --csv or config key csv=...)")
    min_minutes = args.min_minutes if args.min_minutes is not None else as_int("min_minutes", cfg.get("min_minutes", "10"))
    max_minutes = args.max_minutes if args.max_minutes is not None else as_int("max_minutes", cfg.get("max_minutes", "60"))
    days = args.days if args.days is not None else as_int("days", cfg.get("days", "7"))
    ics_file = args.ics_file or cfg.get("ics_file", "wildweeks.ics")
    activities = load_activities(csv_path)
    plan = schedule(activities, days, min_minutes, max_minutes)
    print_table(plan)
    write_ics(plan, ics_file)


if __name__ == "__main__":
    main()
