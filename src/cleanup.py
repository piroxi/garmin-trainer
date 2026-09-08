"""Delete all workouts from the Garmin Connect workout library."""

from garmin import login


def cleanup(client):
    workouts = client.get_workouts()
    if not workouts:
        print("No workouts found.")
        return 0

    print(f"Found {len(workouts)} workouts. Deleting...")
    deleted, skipped = 0, 0
    for i, w in enumerate(workouts):
        name = w.get("workoutName", w.get("name", "?"))
        if "cali" in name.lower():
            skipped += 1
            continue
        wid = w["workoutId"]
        try:
            client.delete_workout(wid)
            deleted += 1
            if (i + 1) % 10 == 0:
                print(f"  {i + 1}/{len(workouts)}...")
        except Exception as e:
            print(f"  FAILED: {name} ({wid}): {e}")

    print(f"Deleted {deleted}, skipped {skipped} (Cali*), total {len(workouts)}.")
    return deleted


if __name__ == "__main__":
    g = login()
    print(f"Logged in: {g.full_name or g.display_name}")
    cleanup(g)
