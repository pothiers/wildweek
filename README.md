# Wildweek

Deterministic CLI scheduler for wildcard activities.

It reads activity data from CSV, builds a day-by-day schedule, prints a text table, and writes a schedule CSV file.

## Input CSV

CSV headers must be:

```csv
name,duration,probability
```

- `name`: activity name
- `duration`: minutes (integer, `>= 0`)
- `probability`: float in `[0,1]`

Example (`wild-events.csv`):

```csv
name,duration,probability
Forest Trail,40,0.45
Birdwatching,30,0.35
Farmers Market,50,0.30
Kayak,60,0.20
Campfire,45,0.40
Stargazing,35,0.55
```

## Command Line

Run:

```bash
python3 scheduler.py --csv wild-events.csv
```

Supported flags:

- `--csv`: input CSV path
- `--config`: config file path (default: `wildweek.conf`)
- `--min_minutes`: minimum daily minutes for wildcard activities (default: `10`)
- `--max_minutes`: maximum daily minutes for wildcard activities (default: `60`)
- `--days`: number of days to schedule (overrides config `weeks`)
- `--ics_file`: output schedule CSV filename (default: `wildweeks.csv`)

## Config File

All parameters can be set in config as `key=value` lines.

Default template file:

```text
# Wildweek default config
# csv=wild-events.csv
# min_minutes=10
# max_minutes=60
# weeks=2
# days=14
# ics_file=wildweeks.csv
# seed=12345
```

Rules:

- Empty lines and `#` comments are ignored.
- CLI args override config values.
- If `days` is not set, scheduler uses `weeks * 7` (default `2` weeks).
- Maximum schedule length is `35` days (5 weeks).
- `seed` is config-only. When set, it enables reproducible shuffled activity ordering.

## Output

The CLI writes:

- Text table to stdout, e.g.:

```text
Day | Total Minutes | Activities
--- | ------------- | ----------
1 (Mon) | 75 | Hike(30), Museum(45)
2 (Tue) | 75 | Hike(30), Cafe(20), Read(25)
```

- CSV schedule file to `--ics_file` path (or `wildweeks.csv` by default).

## Scheduling Behavior

- Deterministic draw function (same inputs produce same schedule).
- An activity appears at most once per day.
- Daily total is constrained by `min_minutes` and `max_minutes` when possible.
- Effective activity probability increases with days since last use.

## Tests

Run:

```bash
python3 -m unittest discover -s tests -v
```

Current test coverage includes:

- CSV parsing
- deterministic scheduling + constraints
- schedule CSV generation
- CLI-over-config precedence
- 35-day cap / 5-week limit behavior
- seeded reproducibility behavior
