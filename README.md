# APSRTC Route 52V/G Live Bus Tracker (Visakhapatnam)

A lightweight, dedicated real-time bus tracking application for Visakhapatnam (Vizag) City Route **52V/G** (*Gollala Endada ⇌ Sagarnagar ⇌ Maddilapalem ⇌ RTC Complex ⇌ Jagadamba ⇌ Town Kotharoad / OHPO*), powered by the open transit data and live GTFS-RT feeds from [reclaimchennai/apsrtc](https://github.com/reclaimchennai/apsrtc).

---

## 🗺️ Route Directions & Corridor Details

The tracker provides **2 dedicated Route Tabs** for both directions of travel:

### 1. ➡️ Route 1 [FROM ➔ TO]: Gollala Endada ➔ Town Kotharoad
- **Total Stops**: 9 Stops (~16.2 km, ~45 min travel time)
- **Stops in sequence**:
  1. 🚏 **Gollala Endada** (Terminal - Stop ID `243841`)
  2. 🚏 **Sagarnagar** (Stop ID `243888`)
  3. 🚏 **B V K College / Visalakshi Nagar** (Stop ID `226115`)
  4. 🚏 **Venkojipalem** (Stop ID `226202`)
  5. 🚏 **Maddilapalem** (Depot / Transit Hub - Stop ID `8351`)
  6. 🚏 **RTC Complex Vsp** (Central Bus Station - Stop ID `232186`)
  7. 🚏 **Jagadamba Centre** (Stop ID `240929`)
  8. 🚏 **Purna Market** (Stop ID `1477289406496`)
  9. 🚏 **Town Kotharoad** (Terminal - Stop ID `1676537881957`)

### 2. ⬅️ Route 2 [TO ➔ FROM]: Town Kotharoad ➔ Gollala Endada
- **Total Stops**: 9 Stops (~16.2 km, ~45 min travel time)
- **Stops in sequence**:
  1. 🚏 **Town Kotharoad** (Terminal - Stop ID `1676537881957`)
  2. 🚏 **Purna Market** (Stop ID `1477289406496`)
  3. 🚏 **Jagadamba Centre** (Stop ID `240929`)
  4. 🚏 **RTC Complex Vsp** (Central Bus Station - Stop ID `232186`)
  5. 🚏 **Maddilapalem** (Depot / Transit Hub - Stop ID `8351`)
  6. 🚏 **Venkojipalem** (Stop ID `226202`)
  7. 🚏 **B V K College / Visalakshi Nagar** (Stop ID `226115`)
  8. 🚏 **Sagarnagar** (Stop ID `243888`)
  9. 🚏 **Gollala Endada** (Terminal - Stop ID `243841`)

---

## ✨ Features Added

- **2 Route Direction Tabs**: Switch between **From ➔ To** (*Gollala Endada ➔ Town Kotharoad*) and **To ➔ From** (*Town Kotharoad ➔ Gollala Endada*).
- **Available Buses per Direction**: Filter and view live buses traveling along each route leg.
- **Stops Count & Interactive Progression**: Displays total stops (9 stops), with a collapsible timeline showing stop names, order, and live bus positions.
- **Where the Bus Currently Is**:
  - Exact nearest stop (e.g. `📍 Currently near: RTC Complex Vsp (~0.4 km away)`)
  - Stop progress: `Stop 6 of 9 • Next: Jagadamba • 3 stops remaining`
  - Visual Step Progress bar with a floating bus icon between origin and destination.
  - Live speed in km/h (`Moving` or `Halted at Stop`), GPS bearing, and next stop ETA.
- **Interactive Leaflet Map**: Dynamic route highlights (`s5718` for forward, `s5719` for return) and directionally numbered stop markers (1-9).
- **Demo / Preview Mode**: Integrated toggle in the header to instantly preview live bus tracking with realistic recorded GPS positions anytime.

---

## 🔍 How the Data Works

APSRTC publishes live GPS positions for all buses via the official *APSRTC Live Track* app. The [reclaimchennai/apsrtc](https://github.com/reclaimchennai/apsrtc) project ingests this stream, standardizes it into standard GTFS-RT 2.0 protocol buffer and JSON feeds, and publishes them with **open CORS headers**:

- **Live Vehicle Positions**: `https://maps.reclaim.city/apsrtc/rt/vehicle_positions.json`
- **Live Trip Updates & ETAs**: `https://maps.reclaim.city/apsrtc/rt/trip_updates.json`
- **Feed Freshness**: `https://maps.reclaim.city/apsrtc/rt/status.json` (Updates every ~15s)

### Why Duty IDs `A024` and `H012`?
In APSRTC's operational fleet management:
- Public buses display **52V** (Sagar Nagar ⇌ OHPO) or **52V/G** (Gollala Endada ⇌ Town Kotharoad).
- The internal duty numbers assigned to Maddilapalem depot buses operating this route are **`A024`** and **`H012`**.
- This tracker matches trips formatted as `A024_*_MADDILAPALEM` and `H012_*_MADDILAPALEM`, or route IDs matching `a024-gollala-endada-town-kotharoad` / `h012-gollala-endada-old-head-post-office`.

---

## 🚀 How to Run the Application

### 1. Web Application (`index.html`)

You can launch the web interface in three different ways:

#### Option A: Direct Open (Zero setup, works immediately)
Double-click `index.html` or open it directly in Google Chrome, Safari, Firefox, or Edge. 
Because the Reclaim Chennai feed has `Access-Control-Allow-Origin: *`, the browser can fetch the live data directly without needing any server!

#### Option B: Using the Python Backend (`server.py`)
Run the lightweight built-in server:
```bash
python3 server.py 8080
```
Then visit in your browser:
👉 **`http://localhost:8080`**

#### Option C: Host on Mobile / Free Cloud
You can deploy `index.html` directly to:
- **GitHub Pages**
- **Vercel / Netlify / Cloudflare Pages**
- Or save it to your phone's home screen as a Web App!

---

### 2. Terminal Live Tracker (`cli_tracker.py`)

If you want a live command-line dashboard directly in your shell:

```bash
# Continuous live refresh every 15 seconds
python3 cli_tracker.py

# One-time snapshot
python3 cli_tracker.py --once
```

**Example output:**
```
======================================================================
  🚌  APSRTC ROUTE 52V/G LIVE BUS TRACKER  —  2026-11-23 16:26:23
  Corridor: Gollala Endada ⇌ Sagarnagar ⇌ Maddilapalem ⇌ Town Kotharoad
======================================================================

  Active buses on Route 52V/G: 2

[1] Bus Number: AP02Z0318  |  Duty/Trip: A024_12_MADDILAPALEM
    Status:      Moving (18.2 km/h) (Heading: 202.9°)
    Direction:   Towards Town Kotharoad
    Near Stop:   RTC Complex Vsp (~0.45 km away)
    Live GPS:    Lat 17.71379, Lon 83.30368  (Updated 16:25:26)
    Predictions: Next ETA: 16:30:00 (+0s)
----------------------------------------------------------------------
[2] Bus Number: AP31Z0167  |  Duty/Trip: H012_5_MADDILAPALEM
    Status:      Halted / Bus Stop (Heading: 0.0°)
    Direction:   Towards Gollala Endada
    Near Stop:   B V K College (~0.11 km away)
    Live GPS:    Lat 17.75551, Lon 83.34272  (Updated 16:25:43)
    Predictions: Next ETA: 16:30:00 (+0s)
----------------------------------------------------------------------
```

---

## ✨ Features

- **Live GPS Tracking**: Real-time position updates, heading arrows, vehicle registration plates (e.g. `AP02Z0318`, `AP31Z0167`), and speed in km/h.
- **Stop Predictions & ETAs**: Arrival estimations at downstream stops using GTFS-RT TripUpdates.
- **Full Route Geometry**: Polylines for the corridor on OpenStreetMap / Leaflet.
- **Proximity Alarm**: Choose your boarding stop (e.g., *Sagarnagar* or *Maddilapalem*); get a browser notification & chime sound when the 52V/G bus approaches within 1.2 km.
- **Timetable Explorer**: Full 36-trip daily schedule with real-time detection of active trips.
- **Locate Me**: Geolocation button showing your distance to the bus and the nearest bus stop.
- **Mobile Optimized**: Responsive touch drawer and full-screen map layout for mobile phones.

---

## 📁 Project Structure

```
.
├── index.html            # Standalone modern web app (Leaflet + Glassmorphism UI)
├── cli_tracker.py        # Terminal live dashboard with auto-refresh
├── server.py             # Python HTTP server + API proxy (/api/live, /api/route)
├── route_52vg_data.json  # Route definitions, coordinates, stops, and timetable
├── README_52VG.md        # Guide and documentation
└── data/                 # Static GTFS feeds from reclaimchennai/apsrtc
```
