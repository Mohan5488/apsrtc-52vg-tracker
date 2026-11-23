#!/usr/bin/env python3
"""
APSRTC 52V/G Live Tracker Backend Server
Pure Python 3 - Zero dependencies required.
Serves web app and provides /api/live endpoint.
"""

import http.server
import socketserver
import urllib.request
import json
import os
import sys

PORT = 8080
VP_FEED_URL = "https://maps.reclaim.city/apsrtc/rt/vehicle_positions.json"
TU_FEED_URL = "https://maps.reclaim.city/apsrtc/rt/trip_updates.json"

ROUTE_IDS = {
    "a024-gollala-endada-town-kotharoad",
    "h012-gollala-endada-old-head-post-office",
    "a024-old-head-post-office-sagarnagar",
    "h012-gollala-endada-maddilapalem",
    "a024-maddilapalem-sagarnagar"
}

def is_route_52vg(entity):
    v = entity.get("vehicle", {})
    trip = v.get("trip", {})
    t_id = trip.get("tripId", "")
    r_id = trip.get("routeId", "")
    if ("A024" in t_id or "H012" in t_id) and "MADDILAPALEM" in t_id:
        return True
    if r_id in ROUTE_IDS:
        return True
    return False

def fetch_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; APSRTC-52VG-Tracker/1.0)"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

class TrackerHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for all responses
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/live":
            self.handle_api_live()
        elif self.path == "/api/route":
            self.handle_api_route()
        else:
            # Default to serving index.html if root
            if self.path == "/":
                self.path = "/index.html"
            super().do_GET()

    def handle_api_route(self):
        try:
            with open("route_52vg_data.json", "r") as f:
                data = json.load(f)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def handle_api_live(self):
        try:
            vp_data = fetch_json(VP_FEED_URL)
            tu_data = fetch_json(TU_FEED_URL)

            matched_buses = []
            for e in vp_data.get("entity", []):
                if is_route_52vg(e):
                    matched_buses.append(e)

            matched_tus = []
            for e in tu_data.get("entity", []):
                tu = e.get("tripUpdate", {})
                t_id = tu.get("trip", {}).get("tripId", "")
                r_id = tu.get("trip", {}).get("routeId", "")
                if (("A024" in t_id or "H012" in t_id) and "MADDILAPALEM" in t_id) or (r_id in ROUTE_IDS):
                    matched_tus.append(e)

            res = {
                "status": "success",
                "total_live_network_buses": len(vp_data.get("entity", [])),
                "matched_52vg_count": len(matched_buses),
                "vehicle_positions": {"entity": matched_buses},
                "trip_updates": {"entity": matched_tus}
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    with socketserver.TCPServer(("", port), TrackerHandler) as httpd:
        print(f"\n=======================================================")
        print(f"  🚌 APSRTC 52V/G Live Tracker Server Running")
        print(f"  Open in browser: http://localhost:{port}")
        print(f"  API Endpoint:    http://localhost:{port}/api/live")
        print(f"=======================================================\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")

if __name__ == "__main__":
    main()
