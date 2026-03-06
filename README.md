# Wildweek

A minimal CLI weekly scheduler with probability-based task selection.

## Version

v0.2

## Usage

```
python3 wildweek.py [tasks.csv] [--daily-limit MINUTES] [--max-week-minutes MINUTES] [--seed N] [--ics FILE]
```

All arguments have defaults from `wildweek.cfg`. CLI arguments override config values.

### Arguments

| Argument | Default | Description |
|---|---|---|
| `csv` | (from config) | Path to tasks CSV file |
| `--daily-limit` | 120 | Max minutes scheduled per day |
| `--max-week-minutes` | 600 | Max total minutes scheduled per week |
| `--seed` | 42 | Random seed for reproducible task selection |
| `--ics` | (from config) | Output ICS filename (omit to skip ICS export) |

### Examples

```
python3 wildweek.py                              # uses wildweek.cfg defaults
python3 wildweek.py tasks.csv --seed 7           # different weekly draw
python3 wildweek.py --ics schedule.ics           # export to ICS
python3 wildweek.py --daily-limit 180 --max-week-minutes 900
```

### Text Output

```
Monday: Walk-a-bout (120min)
Tuesday: Hike (90min), Call friend (25min), Didgeridoo (5min)
Wednesday: Call friend (25min), Didgeridoo (5min)
...
Sunday: Hike (90min)
ICS written to wildweek.ics
```

## Config File

`wildweek.cfg` (INI format) provides defaults for all CLI arguments:

```ini
[wildweek]
csv = tasks.csv
daily_limit = 120
max_week_minutes = 600
seed = 42
ics = wildweek.ics
```

Omit `ics` to disable ICS output by default.

## Input CSV Format

| Column | Type | Description |
|---|---|---|
| `name` | string | Task name |
| `duration` | integer | Duration in minutes |
| `probability` | float 0–1 | Probability task is chosen each day |

### Example tasks.csv

```
name,duration,probability
Hike,90,0.40
Walk-a-bout,120,0.05
Call friend,25,0.35
Tai Chi,10,0.55
Piano,20,0.55
Didgeridoo,5,0.55
Read,25,0.60
```

## Scheduling Algorithm

1. Seed the random number generator with `--seed`.
2. Iterate over days Monday through Sunday.
3. For each day, iterate over tasks in CSV order.
4. For each task, roll against its `probability` — skip if the roll fails.
5. Assign the task to the day if it fits within `daily_limit` and `max_week_minutes`.
6. Days with no tasks assigned are shown as `(rest)`.

The same seed always produces the same schedule. Change the seed for a different weekly draw.

## ICS Export

When `--ics` is provided (or set in config), an ICS file is written suitable for import into Google Calendar or any calendar application. Events are all-day entries starting the next Monday from today's date.

## Specifications Honored

- Probability-based per-day task selection using `probability` column
- Reproducible output via random seed
- 7 fixed days: Monday through Sunday
- Respects `--daily-limit` (minutes per day)
- Respects `--max-week-minutes` (total minutes per week)
- Config file with CLI override for all parameters
- ICS calendar export (no external dependencies)
- Simple CSV input — no external dependencies (stdlib only)
- Under 150 lines of source code
- Duration unit is minutes throughout

## Requirements

- Python 3.6+
- No external dependencies (stdlib only)

## Prompt Used to Generate This Document

> capture progress
