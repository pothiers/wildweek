# Wildweek

A minimal deterministic CLI weekly scheduler.

## Version

v0.1

## Usage

```
python3 wildweek.py <tasks.csv> [--daily-limit MINUTES] [--max-week-minutes MINUTES]
```

### Arguments

| Argument | Default | Description |
|---|---|---|
| `csv` | (required) | Path to tasks CSV file |
| `--daily-limit` | 120 | Max minutes scheduled per day |
| `--max-week-minutes` | 600 | Max total minutes scheduled per week |

### Example

```
python3 wildweek.py tasks.csv --daily-limit 180 --max-week-minutes 900
```

### Output

```
Monday: Hike (90min), Call friend (25min), Didgeridoo (5min)
Tuesday: Hike (90min), Call friend (25min), Didgeridoo (5min)
...
Saturday: (rest)
```

## Input CSV Format

The CSV file must have at least these columns:

| Column | Type | Description |
|---|---|---|
| `name` | string | Task name |
| `duration` | integer | Duration in minutes |

Additional columns (e.g. `probability`) are ignored.

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

Tasks are assigned to days using a greedy, deterministic pass:

1. Iterate over days Monday through Sunday.
2. For each day, iterate over tasks in CSV order.
3. Assign a task to the day if:
   - Adding it would not exceed `daily_limit` for that day.
   - Adding it would not exceed `max_week_minutes` for the week.
4. A task may be assigned to multiple days (tasks repeat across the week).
5. Days with no tasks assigned are shown as `(rest)`.

The schedule is fully deterministic: the same inputs always produce the same output.

## Specifications Honored (v0.1)

- Deterministic output — no randomness or probability weighting
- 7 fixed days: Monday through Sunday
- Respects `--daily-limit` (minutes per day)
- Respects `--max-week-minutes` (total minutes per week)
- Simple CSV input — stdlib `csv` module, no external dependencies
- Under 150 lines of source code
- Duration unit is minutes throughout

## Requirements

- Python 3.6+
- No external dependencies (stdlib only)

## Prompt Used to Generate This Document

> create documentation for the current design. Include the specifications that are honored by this version.
