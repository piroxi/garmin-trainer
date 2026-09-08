# Garmin Trainer

8-week hybrid macrocycle — run + strength — uploaded to your Garmin Connect watch.

## Project layout

```
├── trainer.py              ← entry point, run from here
├── .env                    ← GARMIN_EMAIL, GARMIN_PASSWORD
├── data/
│   ├── run.json            ← pace zones
│   ├── resistance.json     ← exercise templates + 1RM values
│   └── plan.json           ← 8-week schedule
├── src/
│   ├── common.py           ← constants, file loading
│   ├── run.py              ← running workout builder
│   ├── strength.py         ← strength workout builder
│   ├── garmin.py           ← Garmin auth + API calls
│   └── trainer.py          ← main() + argparse
└── garmin/
    ├── garmin-exercises.txt   ← Garmin exercise catalog (display names)
    ├── category-map.json      ← Garmin exercise → category mapping
    └── samples/
        ├── sample.json        ← reference: a working strength workout
        └── sample2.json       ← reference: same, different exercise type
```

## Quick start

```
# 1. Set credentials
echo "GARMIN_EMAIL=you@email.com" >> .env
echo "GARMIN_PASSWORD=yourpassword" >> .env

# 2. Preview — ALWAYS use dry-run during development
python3 trainer.py --dry-run

# 3. Upload next week
python3 trainer.py --weeks 1
```

**Never run without `--dry-run` while testing.** Garmin has a low API rate limit.

## CLI flags

| Flag | Description |
|------|-------------|
| `--dry-run` | Preview only, no API calls |
| `--ping` | Test Garmin credentials |
| `--test-week` | Schedule Week 7 (Balke + 1RM) on the current week |
| `--start-date YYYY-MM-DD` | First Monday (default: next Monday) |
| `--weeks N` | Number of weeks to upload (default: 1) |
| `--day mon/tue/…` | Upload only this weekday |
| `--only run\|strength` | Upload only runs or only strength |

Modes (`--test-week` and `--ping` are mutually exclusive):

```bash
./trainer.py --dry-run                        # preview next week
./trainer.py --weeks 1                        # upload 1 week
./trainer.py --weeks 8                        # upload full 8-week cycle
./trainer.py --test-week                      # schedule benchmarks this week
./trainer.py --only run --day thursday        # just Thursday's run
```

## How it works

`trainer.py` reads `plan.json` and for each scheduled day builds a structured workout JSON (matched to Garmin's internal format), uploads it to your workout library via the Connect API, and schedules it on the calendar date. The watch syncs and displays the workout with pace targets, rep targets, rest timers, and weight targets — everything structured, not just a text note.

## Data files

### `data/run.json` — pace zones

```json
{
    "easy": { "label": "Easy", "min": "8:18", "max": "6:51" },
    "threshold_tempo": { "label": "Threshold/Tempo", "min": "6:38", "max": "6:18" },
    "interval_vo2max": { "label": "Interval/VO₂ Max", "min": "5:28", "max": "5:14" },
    "balke": { "label": "Balke", "max": "5:45" }
}
```

- `min`/`max` are pace ranges (m:ss per km)
- After test week, update from Balke results

### `data/resistance.json` — exercises + 1RM

```json
{
    "pull": {
        "label": "Pull + Front Lever",
        "exercises": [
            { "id": "Tuck Front Lever", "hold": true },
            { "id": "Weighted Pull-ups", "1rm": 10 },
            { "id": "Landmine Rows", "1rm": 67 }
        ]
    },
    ...
}
```

- 4 templates: `pull`, `push`, `legs`, `shoulders`
- `id` must match a Garmin exercise display name (see `garmin/garmin-exercises.txt`)
- `1rm` in kg — used to calculate working weight per phase
- `hold: true` marks an isometric hold — duration = weekly reps × 5 s
- After test week, fill in from 1RM results

### `data/plan.json` — 8-week schedule

```json
{
    "name": "8-Week Hybrid Cycle",
    "phases": [
        {
            "name": "Base",
            "weeks": [1, 1],
            "days": {
                "monday": {
                    "run": { "type": "easy", "duration": { "unit": "min", "value": 60 } },
                    "strength": { "workout": "pull", "sets": 3, "reps": 12, "intensity_pct": 70 }
                },
                "sunday": {
                    "run": { "type": "long", "duration": { "unit": "min", "value": 90 } }
                }
            }
        }
    ]
}
```

**Run entries:**
- `type` — matches a key in `run.json`
- `duration` — `{ "unit": "min", "value": N }` for time-based runs
- `distance` — `{ "unit": "m", "value": N }` for distance-based intervals
- `reps` — interval repetitions (for `interval_vo2max`)

**Strength entries:**
- `workout` — matches a key in `resistance.json`
- `sets`, `reps`, `intensity_pct` — unified across all strength days in a phase
- Working weight: `1rm × intensity_pct / 100`

## 8-week schedule summary

| Week | Phase | Easy runs | Long run | Thursday quality | Strength |
|------|-------|-----------|----------|------------------|----------|
| 1 | Base | 60min ×3 | 90min | 6×400m intervals | 12 reps @70% |
| 2 | Build | 60min ×3 | 120min | 5×600m intervals | 10 reps @74% |
| 3 | Strength + Volume | 60min ×3 | 135min | 4×800m intervals | 8 reps @79% |
| 4 | Performance | 60min ×3 | 150min | 25min tempo | 6 reps @83% |
| 5 | Peak Development | 60min ×3 | 180min | 5×800m intervals | 5 reps @91% |
| 6 | Peak + Specificity | 60min ×3 | 150min | 25min tempo | 4 reps @96% |
| 7 | Test Week | 60min ×3 | 120min | Balke | 2 reps @100% (1RM) |
| 8 | Deload + Maintenance | 60min ×4 | 120min | easy | 12 reps @60% |

Weekly layout (every phase): Mon pull, Tue legs, Wed rest, Thu quality + push, Fri easy, Sat shoulders, Sun long.

## After the cycle (Week 7 tests)

1. Balke result → update pace zones in `data/run.json`
2. 1RM results → update `1rm` in `data/resistance.json`
3. Re-run `./trainer.py --weeks 8`
