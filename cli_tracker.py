#!/usr/bin/env python3
"""
APSRTC 52V/G Live Bus Tracker (CLI)
Dedicated real-time tracker for Vizag Route 52V/G with 2 Route Directions:
1) FROM -> TO (Gollala Endada -> Town Kotharoad)
2) TO -> FROM (Town Kotharoad -> Gollala Endada)
"""

import urllib.request
import json
import time
import math
import sys
import argparse
from datetime import datetime

FEED_VP_URL = "https://maps.reclaim.city/apsrtc/rt/vehicle_positions.json"
FEED_TU_URL = "https://maps.reclaim.city/apsrtc/rt/trip_updates.json"

STOPS_FORWARD = [
    {"name": "Gollala Endada", "lat": 17.77629, "lon": 83.36794, "terminal": True},
    {"name": "Sagarnagar", "lat": 17.76408, "lon": 83.36105, "terminal": False},
    {"name": "B V K College", "lat": 17.75526, "lon": 83.34369, "terminal": False},
    {"name": "Venkojipalem", "lat": 17.74623, "lon": 83.32851, "terminal": False},
    {"name": "Maddilapalem", "lat": 17.73607, "lon": 83.32060, "terminal": False},
    {"name": "RTC Complex Vsp", "lat": 17.72354, "lon": 83.30751, "terminal": False},
    {"name": "Jagadamba", "lat": 17.71079, "lon": 83.30205, "terminal": False},
    {"name": "Purna Market", "lat": 17.70798, "lon": 83.29731, "terminal": False},
    {"name": "Town Kotharoad", "lat": 17.70228, "lon": 83.29459, "terminal": True}
]

STOPS_BACKWARD = [
    {"name": "Town Kotharoad", "lat": 17.70228, "lon": 83.29459, "terminal": True},
    {"name": "Purna Market", "lat": 17.70798, "lon": 83.29731, "terminal": False},
    {"name": "Jagadamba", "lat": 17.71079, "lon": 83.30205, "terminal": False},
    {"name": "RTC Complex Vsp", "lat": 17.72354, "lon": 83.30751, "terminal": False},
    {"name": "Maddilapalem", "lat": 17.73607, "lon": 83.32060, "terminal": False},
    {"name": "Venkojipalem", "lat": 17.74623, "lon": 83.32851, "terminal": False},
    {"name": "B V K College", "lat": 17.75526, "lon": 83.34369, "terminal": False},
    {"name": "Sagarnagar", "lat": 17.76408, "lon": 83.36105, "terminal": False},
    {"name": "Gollala Endada", "lat": 17.77629, "lon": 83.36794, "terminal": True}
]

DEMO_BUSES = [
    {
        "plate": "AP02Z0318",
        "trip_id": "A024_12_MADDILAPALEM",
        "lat": 17.7085,
        "lon": 83.2975,
        "speed_kmh": 24.0,
        "bearing": 200.0,
        "time": "12:45:00",
        "direction_key": "forward",
        "eta_info": "Next ETA: ~3 mins (+0s)",
        "delay_sec": 0
    },
    {
        "plate": "AP31Z0167",
        "trip_id": "H012_5_MADDILAPALEM",
        "lat": 17.71662,
        "lon": 83.30442,
        "speed_kmh": 0.0,
        "bearing": 26.6,
        "time": "12:45:10",
        "direction_key": "backward",
        "eta_info": "Next ETA: ~5 mins (+0s)",
        "delay_sec": 0
    }
]

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def evaluate_stops_progress(lat, lon, stops_list):
    best_dist = float("inf")
    best_idx = 0
    for idx, s in enumerate(stops_list):
        d = haversine_km(lat, lon, s["lat"], s["lon"])
        if d < best_dist:
            best_dist = d
            best_idx = idx

    stop_num = best_idx + 1
    total = len(stops_list)
    remaining = max(0, total - stop_num)
    next_stop = stops_list[best_idx + 1]["name"] if best_idx < total - 1 else "Destination Terminal"
    
    return {
        "nearest_stop": stops_list[best_idx]["name"],
        "stop_num": stop_num,
        "total_stops": total,
        "dist_km": round(best_dist, 2),
        "remaining": remaining,
        "next_stop": next_stop
    }

def resolve_direction(trip_id, route_id, bearing):
    if "old-head-post-office-sagarnagar" in route_id or "maddilapalem-sagarnagar" in route_id:
        return "backward"
    if "gollala-endada-town-kotharoad" in route_id or "gollala-endada-old-head-post-office" in route_id:
        return "forward"
    
    # Check A024 trip id
    import re
    m_a = re.search(r'A024_(\d+)', trip_id)
    if m_a:
        num = int(m_a.group(1))
        return "forward" if (num % 2 == 0) else "backward"

    m_h = re.search(r'H012_(\d+)', trip_id)
    if m_h:
        num = int(m_h.group(1))
        return "forward" if num in [12, 14, 16, 18, 2, 4, 6, 8, 10] else "backward"

    if bearing and bearing > 0:
        return "forward" if (110 <= bearing <= 260) else "backward"

    return "forward"

def is_route_52vg(entity):
    vehicle = entity.get("vehicle", {})
    trip = vehicle.get("trip", {})
    trip_id = trip.get("tripId", "")
    route_id = trip.get("routeId", "")

    if ("A024" in trip_id or "H012" in trip_id) and "MADDILAPALEM" in trip_id:
        return True
    if route_id in [
        "a024-gollala-endada-town-kotharoad",
        "h012-gollala-endada-old-head-post-office",
        "a024-old-head-post-office-sagarnagar",
        "h012-gollala-endada-maddilapalem",
        "a024-maddilapalem-sagarnagar"
    ]:
        return True
    return False

def fetch_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; APSRTC-52VG-Tracker/1.0)"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def fetch_live_data():
    try:
        vp_data = fetch_json(FEED_VP_URL)
        tu_data = fetch_json(FEED_TU_URL)
    except Exception as e:
        print(f"\033[91mError fetching live feeds: {e}\033[0m")
        return []

    tu_map = {}
    for e in tu_data.get("entity", []):
        tu = e.get("tripUpdate", {})
        trip_id = tu.get("trip", {}).get("tripId", "")
        if trip_id:
            tu_map[trip_id] = tu

    buses = []
    for entity in vp_data.get("entity", []):
        if is_route_52vg(entity):
            v = entity.get("vehicle", {})
            pos = v.get("position", {})
            trip = v.get("trip", {})
            veh_info = v.get("vehicle", {})

            trip_id = trip.get("tripId", "")
            route_id = trip.get("routeId", "")
            lat = pos.get("latitude", 0.0)
            lon = pos.get("longitude", 0.0)
            bearing = pos.get("bearing", 0.0)
            speed_ms = pos.get("speed", 0.0)
            speed_kmh = round((speed_ms or 0) * 3.6, 1)
            ts = int(v.get("timestamp", time.time()))
            dt = datetime.fromtimestamp(ts).strftime("%H:%M:%S")

            dir_key = resolve_direction(trip_id, route_id, bearing)
            stops_ref = STOPS_FORWARD if dir_key == "forward" else STOPS_BACKWARD
            progress = evaluate_stops_progress(lat, lon, stops_ref)

            tu = tu_map.get(trip_id, {})
            stu = tu.get("stopTimeUpdate", [])

            next_stop_info = "Next ETA: Estimating..."
            delay_sec = 0
            if stu:
                first_stop = stu[0]
                delay_sec = first_stop.get("arrival", {}).get("delay", 0)
                arr_ts = first_stop.get("arrival", {}).get("time")
                if arr_ts:
                    arr_dt = datetime.fromtimestamp(int(arr_ts)).strftime("%H:%M:%S")
                    next_stop_info = f"Next ETA: {arr_dt} ({delay_sec:+d}s)"

            buses.append({
                "plate": veh_info.get("licensePlate", veh_info.get("label", "Unknown")),
                "trip_id": trip_id,
                "lat": lat,
                "lon": lon,
                "speed_kmh": speed_kmh,
                "bearing": bearing,
                "time": dt,
                "direction_key": dir_key,
                "progress": progress,
                "eta_info": next_stop_info,
                "delay_sec": delay_sec
            })

    return buses

def print_route_section(title, subtitle, stops_list, buses, color_code):
    print(f"\n{color_code}{'='*72}\033[0m")
    print(f"{color_code}  {title}\033[0m")
    print(f"  \033[90m{subtitle} • Total Stops: {len(stops_list)} stops (~16.2 km)\033[0m")
    print(f"{color_code}{'='*72}\033[0m")

    if not buses:
        print("  \033[90mNo active buses currently reporting in this direction.\033[0m")
        return

    print(f"  \033[1;32mAvailable Buses: {len(buses)}\033[0m\n")
    for i, b in enumerate(buses, 1):
        p = b["progress"]
        status_color = "\033[1;32m" if b["speed_kmh"] > 0 else "\033[1;33m"
        state = f"Moving ({b['speed_kmh']} km/h)" if b["speed_kmh"] > 0 else "Halted / Stop"

        # Text progress bar
        step = p["stop_num"]
        total = p["total_stops"]
        bar_len = 20
        filled = int((step / total) * bar_len)
        bar = "─" * filled + "🚌" + "─" * (bar_len - filled)

        print(f"  \033[1;37m[{i}] Bus:\033[0m \033[1;34m{b['plate']}\033[0m  |  \033[1;37mTrip:\033[0m {b['trip_id']}")
        print(f"      Status:           {status_color}{state}\033[0m (Bearing: {b['bearing']}°)")
        print(f"      Current Location: \033[1;36mNear {p['nearest_stop']}\033[0m (~{p['dist_km']} km away)")
        print(f"      Stop Progress:    Stop \033[1;33m{p['stop_num']}\033[0m of \033[1;33m{total}\033[0m  •  Next: \033[1;32m{p['next_stop']}\033[0m ({p['remaining']} stops left)")
        print(f"      Route Progress:   [{stops_list[0]['name']}] {bar} [{stops_list[-1]['name']}]")
        print(f"      Live GPS:         Lat {b['lat']:.5f}, Lon {b['lon']:.5f} (Updated: {b['time']})")
        print(f"      Prediction:       {b['eta_info']}")
        print("  \033[90m" + "-"*68 + "\033[0m")

def print_dashboard(buses):
    print("\033[2J\033[H", end="")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\033[1;36m" + "#"*72 + "\033[0m")
    print(f"\033[1;37m  🚌  APSRTC 52V/G REAL-TIME BUS TRACKER — {now}\033[0m")
    print(f"      \033[1;33mTotal Active Buses on Network: {len(buses)}\033[0m")
    print("\033[1;36m" + "#"*72 + "\033[0m")

    forward_buses = [b for b in buses if b.get("direction_key") == "forward"]
    backward_buses = [b for b in buses if b.get("direction_key") == "backward"]

    # 1. Route Tab 1: From -> To
    print_route_section(
        "➡️  ROUTE TAB 1 [FROM ➔ TO]: Gollala Endada ➔ Town Kotharoad",
        "Via Sagar Nagar, Maddilapalem & Jagadamba",
        STOPS_FORWARD,
        forward_buses,
        "\033[1;34m"
    )

    # 2. Route Tab 2: To -> From
    print_route_section(
        "⬅️  ROUTE TAB 2 [TO ➔ FROM]: Town Kotharoad ➔ Gollala Endada",
        "Via Jagadamba, Maddilapalem & Sagar Nagar",
        STOPS_BACKWARD,
        backward_buses,
        "\033[1;35m"
    )

def main():
    parser = argparse.ArgumentParser(description="Live Tracker for APSRTC Route 52V/G")
    parser.add_argument("--once", action="store_true", help="Print live positions once and exit")
    parser.add_argument("--demo", action="store_true", help="Run with simulated demo buses")
    parser.add_argument("--interval", type=int, default=15, help="Refresh interval in seconds (default: 15)")
    args = parser.parse_args()

    while True:
        if args.demo:
            buses = []
            for db in DEMO_BUSES:
                stops_ref = STOPS_FORWARD if db["direction_key"] == "forward" else STOPS_BACKWARD
                p = evaluate_stops_progress(db["lat"], db["lon"], stops_ref)
                buses.append({**db, "progress": p})
        else:
            buses = fetch_live_data()

        print_dashboard(buses)
        if args.once or args.demo:
            break
        print(f"\n  Auto-refreshing in {args.interval}s... Press Ctrl+C to exit.")
        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nExiting tracker. Bye!")
            break

if __name__ == "__main__":
    main()
