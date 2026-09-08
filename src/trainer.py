#!/usr/bin/env python3
"""Garmin Trainer — read plan.json, upload workouts to Garmin Connect."""

import argparse, sys
from datetime import date, timedelta

from common import DAY_NAMES, load_env, load_json
from run import build_run
from strength import build_strength
from garmin import login, upload
from cleanup import cleanup


def main():
    load_env()
    p = argparse.ArgumentParser(
        description="Garmin Trainer — upload workouts from plan.json to Garmin Connect",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  ./trainer.py --dry-run                        preview next week's schedule
  ./trainer.py --ping                           test Garmin credentials
  ./trainer.py --test-week                      schedule benchmarks (Balke + 1RM) this week
  ./trainer.py --build-all                      upload full cycle starting next Monday
  ./trainer.py --weeks 8                        upload full 8-week cycle starting next Monday
  ./trainer.py --start-date 2026-07-27 --weeks 2   upload 2 weeks from a specific date

modes (mutually exclusive):
  --test-week    schedule Week 7 (test) on the current week
  --ping         test login, print athlete info
  (default)      upload the training schedule""")
    p.add_argument("--test-week", action="store_true", help="schedule this week using the Test Week phase")
    p.add_argument("--build-all", action="store_true", help="upload the full cycle starting next Monday")
    p.add_argument("--cleanup", action="store_true", help="delete ALL workouts from Garmin library")
    p.add_argument("--only", choices=["run", "strength"], help="upload only runs or only strength")
    p.add_argument("--ping", action="store_true", help="test Garmin credentials and exit")
    p.add_argument("--start-date", metavar="YYYY-MM-DD", help="first Monday of the schedule (default: next Monday)")
    p.add_argument("--weeks", type=int, default=1, help="number of weeks to upload starting from Week 1 (default: 1)")
    p.add_argument("--week", type=int, metavar="N", help="upload only week N of the plan (e.g. --week 3)")
    p.add_argument("--day", choices=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"], help="upload only this weekday")
    p.add_argument("--dry-run", action="store_true", help="preview only, don't upload")
    args = p.parse_args()

    if args.test_week and args.ping:
        sys.exit("--test-week and --ping are mutually exclusive")

    if args.ping:
        try:
            g = login()
            print(f"OK — {g.full_name or g.display_name}")
        except Exception as e:
            sys.exit(f"Auth failed: {e}")
        return

    if args.cleanup:
        client = login()
        print(f"Logged in: {client.full_name or client.display_name}")
        cleanup(client)
        return

    if args.dry_run:
        client = None
    else:
        client = login()
        print(f"Logged in: {client.full_name or client.display_name}")

    zones = load_json("run.json")
    workouts = load_json("resistance.json")
    plan = load_json("plan.json")

    if args.build_all:
        args.weeks = plan.get("weeks") or len(plan["phases"])

    if args.start_date:
        start = date.fromisoformat(args.start_date)
    elif args.test_week:
        start = date.today()
    else:
        today = date.today()
        d = (7 - today.weekday()) % 7 or 7
        start = today + timedelta(days=d)

    if args.week:
        args.weeks = 1
        offset = (args.week - 1) % (plan.get("weeks") or len(plan["phases"]))
        start = start + timedelta(weeks=offset)

    if args.test_week:
        tw = next(p for p in plan["phases"] if p["name"] == "Test Week")
        today = date.today()
        wstart = today - timedelta(days=today.weekday())
        uploaded = 0
        print(f"\n=== Test Week (from plan, mapped to {wstart} – {wstart + timedelta(days=6)}) ===")

        for i, dn in enumerate(DAY_NAMES):
            if args.day and dn != args.day:
                continue
            day = tw["days"].get(dn, {})
            dd = wstart + timedelta(days=i)
            ds = dd.isoformat()

            run = day.get("run")
            if run and run.get("type") == "balke" and args.only != "strength":
                wk = build_run({"type": "balke"}, {"balke": zones["balke"]})
                if not args.dry_run:
                    upload(client, wk, ds)
                print(f"[{dd}] {wk['workoutName']}")
                uploaded += 1

            for wkey in (day.get("workouts") or []):
                if args.only == "run":
                    continue
                sw = build_strength({"workout": wkey, "sets": 1, "reps": 2}, workouts, omit_weight=True)
                sw["workoutName"] = f"1RM Test — {sw['workoutName']}"
                sw["description"] = sw["description"].replace(": 1x2", ": test 1RM")
                if not args.dry_run:
                    upload(client, sw, ds)
                print(f"[{dd}] {sw['workoutName']}")
                uploaded += 1

            s = day.get("strength")
            if s and s.get("workout") and args.only != "run":
                s = dict(s)
                s["intensity_pct"] = 100
                s["reps"] = 2
                sw = build_strength(s, workouts, omit_weight=True)
                sw["workoutName"] = f"1RM Test — {sw['workoutName']}"
                sw["description"] = sw["description"].replace(f": {s['sets']}x2", ": test 1RM")
                if not args.dry_run:
                    upload(client, sw, ds)
                print(f"[{dd}] {sw['workoutName']}")
                uploaded += 1

        print(f"\n{'Would upload' if args.dry_run else 'Uploaded'} {uploaded} workouts")
        return

    # Regular schedule
    print(f"\n=== Weeks starting {start} ===")
    uploaded = 0
    for w in range(args.weeks):
        total_weeks = plan.get("weeks") or len(plan["phases"])
        week_num = ((w + (args.week - 1 if args.week else 0)) % total_weeks) + 1
        phase = next((p for p in plan["phases"] if p["weeks"][0] <= week_num <= p["weeks"][1]), None)
        if not phase:
            continue
        ws = start + timedelta(weeks=w)
        for i, dn in enumerate(DAY_NAMES):
            day = phase["days"].get(dn)
            if not day or (args.day and dn != args.day):
                continue
            dd = ws + timedelta(days=i)
            ds = dd.isoformat()

            run = day.get("run")
            if run and run.get("type") and args.only != "strength":
                wk = build_run(run, zones)
                if wk:
                    if not args.dry_run:
                        try:
                            upload(client, wk, ds)
                        except Exception as e:
                            print(f"  ERROR: {e}")
                    print(f"[{dd}] {wk['workoutName']}")
                    uploaded += 1

            strength = day.get("strength")
            if strength and strength.get("workout") and args.only != "run":
                sw = build_strength(strength, workouts)
                if sw:
                    if not args.dry_run:
                        try:
                            upload(client, sw, ds)
                        except Exception as e:
                            print(f"  ERROR: {e}")
                    print(f"[{dd}] {sw['workoutName']}")
                    uploaded += 1

    print(f"\n{'Would upload' if args.dry_run else 'Uploaded'} {uploaded} workouts")


if __name__ == "__main__":
    main()
