#!/usr/bin/env python3
"""
APSRTC 52V/G Live Bus Tracker (CLI)
Dedicated real-time tracker for Vizag Route 52V/G
(Gollala Endada <-> Sagarnagar <-> Maddilapalem <-> Jagadamba <-> Town Kotharoad / OHPO)
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

STOPS = [
    {"name": "Gollala Endada", "lat": 17.77629, "lon": 83.36794},
    {"name": "Sagarnagar", "lat": 17.76408, "lon": 83.36105},
    {"name": "B V K College", "lat": 17.75526, "lon": 83.34369},
    {"name": "Venkojipalem", "lat": 17.74623, "lon": 83.32851},
    {"name": "Maddilapalem", "lat": 17.73607, "lon": 83.32060},
    {"name": "RTC Complex Vsp", "lat": 17.72354, "lon": 83.30751},
    {"name": "Jagadamba", "lat": 17.71079, "lon": 83.30205},
    {"name": "Purna Market", "lat": 17.70798, "lon": 83.29731},
    {"name": "Town Kotharoad", "lat": 17.70228, "lon": 83.29459},
    {"name": "Old Head Post Office", "lat": 17.67377, "lon": 83.29213}
]

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def find_nearest_stop(lat, lon):
    best_dist = float("inf")
    best_stop = None
    for s in STOPS:
        d = haversine_km(lat, lon, s["lat"], s["lon"])
        if d < best_dist:
            best_dist = d
            best_stop = s
    return best_stop, best_dist

def is_route_52vg(entity):
    vehicle = entity.get("vehicle", {})
    trip = vehicle.get("trip", {})
    trip_id = trip.get("tripId", "")
    route_id = trip.get("routeId", "")

    # Matches Maddilapalem duty A024 or H012
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

    # Map trip updates by tripId
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
            lat = pos.get("latitude", 0.0)
            lon = pos.get("longitude", 0.0)
            bearing = pos.get("bearing", 0.0)
            speed_ms = pos.get("speed", 0.0)
            speed_kmh = round((speed_ms or 0) * 3.6, 1)
            ts = int(v.get("timestamp", time.time()))
            dt = datetime.fromtimestamp(ts).strftime("%H:%M:%S")

            nearest_stop, stop_dist = find_nearest_stop(lat, lon)
            tu = tu_map.get(trip_id, {})
            stu = tu.get("stopTimeUpdate", [])

            next_stop_info = "Calculating..."
            delay_sec = 0
            if stu:
                first_stop = stu[0]
                delay_sec = first_stop.get("arrival", {}).get("delay", 0)
                arr_ts = first_stop.get("arrival", {}).get("time")
                if arr_ts:
                    arr_dt = datetime.fromtimestamp(int(arr_ts)).strftime("%H:%M:%S")
                    next_stop_info = f"Next ETA: {arr_dt} ({delay_sec:+d}s)"

            # Direction heuristic
            route_id = trip.get("routeId", "")
            direction = "Towards Town Kotharoad" if "town-kotharoad" in route_id else "Towards Endada / Sagar Nagar"
            if "17_" in trip_id:
                direction = "Towards Sagarnagar"
            elif "16_" in trip_id:
                direction = "Towards OHPO"

            buses.append({
                "plate": veh_info.get("licensePlate", veh_info.get("label", "Unknown")),
                "trip_id": trip_id,
                "lat": lat,
                "lon": lon,
                "speed_kmh": speed_kmh,
                "bearing": bearing,
                "time": dt,
                "nearest_stop": nearest_stop["name"] if nearest_stop else "Unknown",
                "stop_dist_km": round(stop_dist, 2),
                "direction": direction,
                "eta_info": next_stop_info,
                "delay_sec": delay_sec
            })

    return buses

def print_dashboard(buses):
    print("\033[2J\033[H", end="") # clear screen
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\033[1;36m" + "="*70 + "\033[0m")
    print(f"\033[1;32m  🚌  APSRTC ROUTE 52V/G LIVE BUS TRACKER  —  {now}\033[0m")
    print(f"\033[1;33m  Corridor: Gollala Endada ⇌ Sagarnagar ⇌ Maddilapalem ⇌ Town Kotharoad\033[0m")
    print("\033[1;36m" + "="*70 + "\033[0m\n")

    if not buses:
        print("\033[93m  ⚠️  No 52V/G buses currently broadcasting GPS on the road.\033[0m")
        print("  (Buses usually run from 05:00 AM to 10:30 PM daily)\n")
        return

    print(f"  \033[1;37mActive buses on Route 52V/G:\033[0m \033[1;32m{len(buses)}\033[0m\n")

    for i, b in enumerate(buses, 1):
        status_color = "\033[1;32m" if b["speed_kmh"] > 0 else "\033[1;33m"
        state = f"Moving ({b['speed_kmh']} km/h)" if b["speed_kmh"] > 0 else "Halted / Bus Stop"
        print(f"\033[1;37m[{i}] Bus Number:\033[0m \033[1;34m{b['plate']}\033[0m  |  \033[1;37mDuty/Trip:\033[0m {b['trip_id']}")
        print(f"    Status:      {status_color}{state}\033[0m (Heading: {b['bearing']}°)")
        print(f"    Direction:   \033[1;35m{b['direction']}\033[0m")
        print(f"    Near Stop:   \033[1;36m{b['nearest_stop']}\033[0m (~{b['stop_dist_km']} km away)")
        print(f"    Live GPS:    Lat {b['lat']:.5f}, Lon {b['lon']:.5f}  (Updated {b['time']})")
        print(f"    Predictions: {b['eta_info']}")
        print("\033[90m" + "-"*70 + "\033[0m")

def main():
    parser = argparse.ArgumentParser(description="Live Tracker for APSRTC Route 52V/G")
    parser.add_argument("--once", action="store_true", help="Print live positions once and exit")
    parser.add_argument("--interval", type=int, default=15, help="Refresh interval in seconds (default: 15)")
    args = parser.parse_args()

    while True:
        buses = fetch_live_data()
        print_dashboard(buses)
        if args.once:
            break
        print(f"\n  Auto-refreshing in {args.interval}s... Press Ctrl+C to exit.")
        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nExiting tracker. Bye!")
            break

if __name__ == "__main__":
    main()
