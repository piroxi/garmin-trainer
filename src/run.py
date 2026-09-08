"""Running workout builder."""

from common import COND_DISTANCE, COND_TIME, STEP_INTERVAL, STEP_RECOVERY, STEP_REPEAT, ST_RUN, TARGET_PACE


def _pace_to_target(pace):
    m, s = pace.split(":")
    return round(1000 / (int(m) * 60 + int(s)), 2)


def _step(order, duration=None, distance=None, pace=None, pace_min=None, pace_max=None, step_type=STEP_INTERVAL):
    s = {
        "type": "ExecutableStepDTO", "stepOrder": order,
        "stepType": {"stepTypeId": step_type, "stepTypeKey": {STEP_INTERVAL: "interval", STEP_RECOVERY: "recovery"}.get(step_type, "interval")},
    }
    if duration:
        s["endCondition"] = {"conditionTypeId": COND_TIME, "conditionTypeKey": "time"}
        s["endConditionValue"] = duration
    elif distance:
        s["endCondition"] = {"conditionTypeId": COND_DISTANCE, "conditionTypeKey": "distance"}
        s["endConditionValue"] = distance
    if pace or pace_min:
        s["targetType"] = {"workoutTargetTypeId": TARGET_PACE, "workoutTargetTypeKey": "pace_zone"}
        s["targetValueOne"] = _pace_to_target(pace_max) if pace_max else _pace_to_target(pace)
        s["targetValueTwo"] = _pace_to_target(pace_min) if pace_min else s["targetValueOne"]
    return s


def _segment(steps):
    return {"segmentOrder": 1, "sportType": {"sportTypeId": ST_RUN, "sportTypeKey": "running", "displayOrder": 1}, "workoutSteps": steps}


def build_run(entry, zones):
    t = entry["type"]
    z = zones.get(t) or zones["easy"]
    dur = entry.get("duration", {}).get("value")

    if t in ("easy", "long"):
        s = dur * 60
        label = "Long" if t == "long" else "Easy"
        return {"workoutName": f"{label} Run ({dur} min)", "description": f"{label.lower()} run {dur} min @ {z['min']}-{z['max']}/km",
                "estimatedDurationInSecs": s, "sportType": {"sportTypeId": ST_RUN, "sportTypeKey": "running"},
                "workoutSegments": [_segment([_step(1, duration=s, pace_min=z["min"], pace_max=z["max"])])]}

    if t == "interval_vo2max":
        reps = entry["reps"]
        dist = entry["distance"]["value"]
        return {"workoutName": f"Intervals: {reps}x{dist}m", "description": f"Intervals {reps}x{dist}m @ {z['min']}-{z['max']}/km",
                "estimatedDurationInSecs": reps * (dist + 180), "sportType": {"sportTypeId": ST_RUN, "sportTypeKey": "running"},
                "workoutSegments": [_segment([{
                    "type": "RepeatGroupDTO", "stepOrder": 1,
                    "stepType": {"stepTypeId": STEP_REPEAT, "stepTypeKey": "repeat"},
                    "numberOfIterations": reps, "smartRepeat": False,
                    "workoutSteps": [
                        _step(1, distance=dist, pace_min=z["min"], pace_max=z["max"]),
                        _step(2, duration=180, step_type=STEP_RECOVERY),
                    ],
                }])]}

    if t == "threshold_tempo":
        s = dur * 60
        return {"workoutName": f"Threshold Run ({dur} min)", "description": f"Threshold run {dur} min @ {z['min']}-{z['max']}/km",
                "estimatedDurationInSecs": s, "sportType": {"sportTypeId": ST_RUN, "sportTypeKey": "running"},
                "workoutSegments": [_segment([_step(1, duration=s, pace_min=z["min"], pace_max=z["max"])])]}

    if t == "balke":
        p = z["max"]
        return {"workoutName": "Balke Test", "description": f"15 min Balke test @ {p}/km target",
                "estimatedDurationInSecs": 900, "sportType": {"sportTypeId": ST_RUN, "sportTypeKey": "running"},
                "workoutSegments": [_segment([_step(1, duration=900, pace=p)])]}
