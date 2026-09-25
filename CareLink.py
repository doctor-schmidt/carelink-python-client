import carelink_client2
from datetime import datetime

# ------------------------------------------------------------
# Get data directly from CareLink
# ------------------------------------------------------------
client = carelink_client2.CareLinkClient(tokenFile="logindata.json")

if not client.init():
    print("ERROR: Unable to initialize CareLink client")
    raise SystemExit(1)

data = client.getRecentData()

if data is None:
    print(
        f"ERROR: Unable to get CareLink data "
        f"(response code {client.getLastResponseCode()})"
    )
    raise SystemExit(1)


# ------------------------------------------------------------
# Extract events
# ------------------------------------------------------------
markers = data.get("patientData", {}).get("markers", [])

events = []

for marker in markers:
    marker_type = marker.get("type")
    timestamp = marker.get("timestamp")

    if not timestamp:
        continue

    values = marker.get("data", {}).get("dataValues", {})

    if marker_type == "BG_READING":
        raw_value = values.get("unitValue")

        if raw_value is not None:
            raw_value = float(raw_value)
            glucose_mmol = raw_value / 18.0

            events.append({
                "timestamp": timestamp,
                "type": "BG",
                "mgdl": raw_value,
                "mmol": glucose_mmol,
            })

    elif marker_type == "MANUAL_BOLUS":
        insulin = values.get("insulinUnits")

        if insulin is not None:
            events.append({
                "timestamp": timestamp,
                "type": "INSULIN",
                "units": float(insulin),
                "insulin_type": values.get("insulinType", ""),
            })


# ------------------------------------------------------------
# Today
# ------------------------------------------------------------
now = datetime.now()
today = now.date()

today_events = [
    e for e in events
    if datetime.fromisoformat(e["timestamp"]).date() == today
]

today_bg = [
    e for e in today_events
    if e["type"] == "BG"
]

today_insulin = [
    e for e in today_events
    if e["type"] == "INSULIN"
]


# Sort newest first for display
today_events.sort(
    key=lambda e: e["timestamp"],
    reverse=True
)


# ------------------------------------------------------------
# Statistics
# ------------------------------------------------------------
print()
print("=" * 65)
print(f"CARELINK — {today.strftime('%Y-%m-%d')}")
print("=" * 65)

if today_bg:
    glucose_values = [e["mmol"] for e in today_bg]

    average = sum(glucose_values) / len(glucose_values)
    minimum = min(glucose_values)
    maximum = max(glucose_values)

    print(f"Glucose readings : {len(glucose_values)}")
    print(f"Average glucose  : {average:.1f} mmol/L")
    print(f"Minimum          : {minimum:.1f} mmol/L")
    print(f"Maximum          : {maximum:.1f} mmol/L")
else:
    print("Glucose readings : 0")

print(f"Insulin injections: {len(today_insulin)}")

if today_insulin:
    total_insulin = sum(e["units"] for e in today_insulin)
    print(f"Total insulin     : {total_insulin:.1f} u")
else:
    total_insulin = 0


# ------------------------------------------------------------
# Event list
# ------------------------------------------------------------
print()
print("-" * 65)
print("EVENTS")
print("-" * 65)

last_bgv = "--"

print()

for event in today_events:

    dt = datetime.fromisoformat(event["timestamp"])
    time = dt.strftime("%H:%M")

    if event["type"] == "BG":

        print(
            f"{time}   Glucose   "
            f"{event['mmol']:.1f} mmol/L "
            f"({event['mgdl']:.0f} mg/dL)"
        )

        if last_bgv == "--":
            last_bgv = f"{event['mmol']:.1f}"


print()

for event in today_events:

    dt = datetime.fromisoformat(event["timestamp"])
    time = dt.strftime("%H:%M")

    if event["type"] != "BG":

        print(
            f"{time}   Insulin    "
            f"{event['units']:.1f} u"
        )


# ------------------------------------------------------------
# Last injection
# ------------------------------------------------------------
if today_insulin:

    last_injection = max(
        today_insulin,
        key=lambda e: e["timestamp"]
    )

    injection_time = datetime.fromisoformat(
        last_injection["timestamp"]
    )

    elapsed = now - injection_time

    total_minutes = int(
        elapsed.total_seconds() // 60
    )

    hours = total_minutes // 60
    minutes = total_minutes % 60

    print()
    print("=" * 65)

    print(
        f"Last:    {last_bgv}       "
        f"( {total_insulin:.0f}u"
        f"   {len(today_insulin)}   "
        f"{last_injection['units']:.0f}u "
        f"{hours}{minutes:02d} )"
    )

    print("=" * 65)

else:

    print()
    print("=" * 65)

    print(
        f"Last:    {last_bgv}       "
        f"( {total_insulin:.0f}u"
        f"     Last injection: none today )"
    )

    print("=" * 65)

print()