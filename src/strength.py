"""Strength workout builder."""

from common import COND_REPS, COND_TIME, STEP_INTERVAL, STEP_REPEAT, ST_STRENGTH

STEP_REST = 5

_NO_TARGET = {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"}
_DUMMY_STROKE = {"strokeTypeId": 0, "strokeTypeKey": None, "displayOrder": 0}
_DUMMY_EQUIP = {"equipmentTypeId": 0, "equipmentTypeKey": None, "displayOrder": 0}
_KG_UNIT = {"unitId": 8, "unitKey": "kilogram", "factor": 1000.0}

_EXERCISE_KEYS = {
    "Tuck Front Lever":              ("MODIFIED_FRONT_LEVER",            "CORE"),
    "Weighted Pull-ups":             ("WEIGHTED_PULL_UP",                "PULL_UP"),
    "Landmine Rows":                 ("T_BAR_ROW",                       "ROW"),
    "Feet-Elevated Inverted Rows":   ("ELEVATED_FEET_INVERTED_ROW",      "ROW"),
    "Bicep Curls":                   ("DUMBBELL_BICEPS_CURL",            "CURL"),
    "Tuck Planche":                  ("STRAIGHT_ARM_PLANK",              "PLANK"),
    "Incline Dumbbell Bench Press":  ("INCLINE_DUMBBELL_BENCH_PRESS",    "BENCH_PRESS"),
    "Parallel Bar Dips":             ("WEIGHTED_DIP",                    "TRICEPS_EXTENSION"),
    "Pseudo-Planche Push-ups":       ("PIKE_PUSH_UP",                    "PUSH_UP"),
    "Tricep Pushdowns":              ("TRICEPS_PRESSDOWN",               "TRICEPS_EXTENSION"),
    "Romanian Deadlift":             ("ROMANIAN_DEADLIFT",               "DEADLIFT"),
    "Front Squat":                   ("BARBELL_FRONT_SQUAT",             "SQUAT"),
    "Dumbbell Bulgarian Split Squat": ("DUMBBELL_BULGARIAN_SPLIT_SQUAT", "LUNGE"),
    "Standing Calf Raise":           ("STANDING_CALF_RAISE",             "CALF_RAISE"),
    "Hanging Leg Raise":             ("HANGING_LEG_RAISE",               "LEG_RAISE"),
    "HSPU Progression":              ("HANDSTAND_PUSH_UP",               "PUSH_UP"),
    "Straight-Arm Lat Pulldown":     ("STRAIGHT_ARM_PULLDOWN",           "PULL_UP"),
    "Overhead Dumbbell Press":       ("OVERHEAD_DUMBBELL_PRESS",         "SHOULDER_PRESS"),
    "DB Lateral Raise":              ("DUMBBELL_LATERAL_RAISE",          "LATERAL_RAISE"),
    "Face Pull":                     ("FACE_PULL",                       "ROW"),
}


HOLD_SECS_PER_REP = 5  # ponytail: hold time = weekly reps × this; tune if holds too short/long


def _build_step(ex, reps, pct, omit_weight):
    name = ex["id"]
    w = None
    if not omit_weight and ex.get("1rm") and pct:
        w = round(ex["1rm"] * pct / 100)
    ek = _EXERCISE_KEYS.get(name, (name.upper().replace(" ", "_").replace("-", "_"), ""))
    st = {
        "type": "ExecutableStepDTO",
        "stepType": {"stepTypeId": STEP_INTERVAL, "stepTypeKey": "interval"},
        "targetType": _NO_TARGET,
        "strokeType": _DUMMY_STROKE,
        "equipmentType": _DUMMY_EQUIP,
        "exerciseName": ek[0],
        "category": ek[1],
    }
    if ex.get("hold"):
        st["endCondition"] = {"conditionTypeId": COND_TIME, "conditionTypeKey": "time"}
        st["endConditionValue"] = reps * HOLD_SECS_PER_REP
    else:
        st["endCondition"] = {"conditionTypeId": COND_REPS, "conditionTypeKey": "reps"}
        st["endConditionValue"] = reps
        if w:
            st["weightValue"] = float(w)
            st["weightUnit"] = _KG_UNIT
    return st


def _rest_step():
    return {
        "type": "ExecutableStepDTO",
        "stepType": {"stepTypeId": STEP_REST, "stepTypeKey": "rest"},
        "endCondition": {"conditionTypeId": COND_TIME, "conditionTypeKey": "time"},
        "endConditionValue": 120,
        "targetType": _NO_TARGET,
        "strokeType": _DUMMY_STROKE,
        "equipmentType": _DUMMY_EQUIP,
    }


def build_strength(strength, workouts, omit_weight=False):
    wk = workouts[strength["workout"]]
    sets = strength["sets"]
    reps = strength["reps"]
    pct = strength.get("intensity_pct")

    repeat_groups = []
    order = 1
    for ex in wk["exercises"]:
        rg = {
            "type": "RepeatGroupDTO", "stepOrder": order,
            "stepType": {"stepTypeId": STEP_REPEAT, "stepTypeKey": "repeat"},
            "numberOfIterations": sets, "smartRepeat": False,
            "endCondition": {"conditionTypeId": 7, "conditionTypeKey": "iterations"},
            "endConditionValue": sets,
            "workoutSteps": [
                _build_step(ex, reps, pct, omit_weight),
                _rest_step(),
            ],
        }
        rg["workoutSteps"][0]["stepOrder"] = 1
        rg["workoutSteps"][1]["stepOrder"] = 2
        repeat_groups.append(rg)
        order += 1

    total_secs = sets * len(wk["exercises"]) * (reps * 4 + 120)
    desc_lines = []
    for ex in wk["exercises"]:
        if ex.get("hold"):
            desc_lines.append(f"{ex['id']}: {sets}x{reps * HOLD_SECS_PER_REP}s")
            continue
        w = ""
        if not omit_weight and ex.get("1rm") and pct:
            w = f" @ {ex['1rm'] * pct / 100:.0f} kg"
        desc_lines.append(f"{ex['id']}: {sets}x{reps}{w}")
    if strength.get("note"):
        desc_lines.append(strength["note"])

    return {
        "workoutName": wk["label"], 
        "description": "\n".join(desc_lines),
        "estimatedDurationInSecs": total_secs,
        "sportType": {"sportTypeId": ST_STRENGTH, "sportTypeKey": "strength_training"},
        "workoutSegments": [
            {
                "segmentOrder": 1,
                "sportType": {
                    "sportTypeId": ST_STRENGTH,
                    "sportTypeKey": 
                    "strength_training",
                    "displayOrder": 1
                }, 
                "workoutSteps": repeat_groups
            }
        ],
    }
