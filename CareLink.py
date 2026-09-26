
import logging
logging.disable(logging.INFO)

import carelink_client2
from datetime import datetime

client = carelink_client2.CareLinkClient(
    tokenFile="logindata.json"
)

if not client.init():
    print("CareLink initialization failed")
    raise SystemExit

data = client.getRecentData()

markers = data.get("patientData", {}).get("markers", [])

today = datetime.now().date()

injections = []
total = 0.0

for marker in markers:
    if marker.get("type") != "MANUAL_BOLUS":
        continue

    timestamp = marker.get("timestamp")
    if not timestamp:
        continue

    dt = datetime.fromisoformat(
        timestamp.replace("Z", "+00:00")
    ).astimezone()
        
    if dt.date() != today:
        continue

    data_values = marker.get("data", {}).get("dataValues", {})
    insulin_units = data_values.get("insulinUnits")

    if insulin_units is None:
        continue

    amount = float(insulin_units)

    elapsed_minutes = int(
        (datetime.now().astimezone() - dt).total_seconds() // 60
    )

    injections.append({
        "time": dt.strftime("%H:%M"),
        "units": amount,
        "elapsed": elapsed_minutes
    })

    total += amount


# Last injection
if injections:
    last = injections[0]

    # Find the actual timestamp of the most recent injection
    last_marker = None
    last_dt = None

    for marker in markers:
        if marker.get("type") != "MANUAL_BOLUS":
            continue

        timestamp = marker.get("timestamp")
        if not timestamp:
            continue

        marker_dt = datetime.fromisoformat(
            timestamp.replace("Z", "+00:00")
        ).astimezone()

        if last_dt is None or marker_dt > last_dt:
            last_dt = marker_dt

    if last_dt:
        elapsed = datetime.now().astimezone() - last_dt
        minutes = int(elapsed.total_seconds() // 60)

        hours = minutes // 60
        mins = minutes % 60

    print()
    print(f"( {total:g}u   {len(injections)}   {last['units']:g}u {hours:01d}{mins:02d} )")
    print("--------------------")
    
    for injection in injections:
        minutes = injection["elapsed"]
        hours = minutes // 60
        mins = minutes % 60
    
        print(
            f"{injection['time']}   "
            f"{injection['units']:g}u "
            f"{hours}{mins:02d}"
        )
    
    print("--------------------")
    



