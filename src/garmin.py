"""Garmin Connect auth and API calls."""

import os, sys
from garminconnect import Garmin, GarminConnectAuthenticationError, GarminConnectTooManyRequestsError


def login():
    email = os.environ["GARMIN_EMAIL"]
    password = os.environ["GARMIN_PASSWORD"]
    client = Garmin(email, password, prompt_mfa=lambda: input("MFA code: "))
    try:
        client.login()
    except GarminConnectAuthenticationError:
        sys.exit("Auth failed")
    except GarminConnectTooManyRequestsError:
        sys.exit("Rate limited. Wait a few minutes.")
    return client


def upload(client, wk, date_str):
    r = client.upload_workout(wk)
    client.schedule_workout(r["workoutId"], date_str)
