"""
CLI Demonstration & Verification Script for Martian Routing Engine.
Executes representative Jezero Crater expedition routes and prints analytical reports.
"""

import sys
import os
import time

# Set utf-8 encoding for cross-platform Windows terminal compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from terrain import get_terrain
from router import MartianRouter
from models import Coordinate, RoutingWeights


def run_mission_demo(name: str, start: Coordinate, end: Coordinate, max_safe_slope: float = 20.0):
    print("\n" + "=" * 75)
    print(f"[MISSION SIMULATION] {name}")
    print(f"   Start: ({start.lat:.4f} N, {start.lon:.4f} E)  -->  Destination: ({end.lat:.4f} N, {end.lon:.4f} E)")
    print(f"   Max Traversable Slope Constraint: {max_safe_slope:.1f} deg")
    print("=" * 75)

    terrain = get_terrain()
    router = MartianRouter(terrain)

    t0 = time.perf_counter()
    response = router.route_mission(
        start=start,
        end=end,
        max_safe_slope=max_safe_slope,
        weights=RoutingWeights(distance=1.0, slope_penalty=4.0, hazard_penalty=4.5)
    )
    duration_ms = (time.perf_counter() - t0) * 1000.0

    direct = response.direct_path
    safe = response.safe_survival_path

    print(f"\n[TIMER] Routing Computation Time: {duration_ms:.2f} ms")

    print("\n[1] DIRECT PATH TRAJECTORY (No Hazard Avoidance):")
    print(f"    * Total Traversal Distance : {direct.total_distance_m:,.1f} meters ({direct.total_distance_m/1000.0:.2f} km)")
    print(f"    * Peak Slope Encountered   : {direct.max_slope_deg:.2f} deg")
    print(f"    * Elevation Profile        : Start={direct.elevation_array[0]:.1f}m -> Min={min(direct.elevation_array):.1f}m -> Max={max(direct.elevation_array):.1f}m -> End={direct.elevation_array[-1]:.1f}m")
    print("    * Hazard Warnings Logged   :")
    for warn in direct.hazard_warnings:
        print(f"      [WARNING] {warn}")

    print("\n[2] SAFE SURVIVAL PATH (Weighted 8-Directional A* Detour):")
    print(f"    * Total Traversal Distance : {safe.total_distance_m:,.1f} meters ({safe.total_distance_m/1000.0:.2f} km)")
    print(f"    * Peak Slope Encountered   : {safe.max_slope_deg:.2f} deg (Enforced <= {max_safe_slope:.1f} deg)")
    print(f"    * Estimated EVA Transit    : {safe.estimated_eva_time_mins:.1f} minutes")
    print(f"    * Tactical Detour Overhead : +{safe.detour_percentage:.1f}% extra distance")
    print(f"    * Waypoints Count          : {len(safe.coordinates)} path nodes")

    print("\n[3] EXECUTIVE SURVIVAL SUMMARY:")
    print(f"    {response.comparison_summary}")


if __name__ == "__main__":
    print("Initializing Jezero Crater 2D Terrain Model (NASA Space Apps 2026)...")
    
    # Mission 1: Perseverance Landing Base -> Kodiak Butte (Western Delta)
    run_mission_demo(
        name="EXPEDITION 1: Base Alpha -> Kodiak Butte Delta Front",
        start=Coordinate(lat=18.380, lon=77.580),
        end=Coordinate(lat=18.445, lon=77.455),
        max_safe_slope=20.0
    )

    # Mission 2: Traverse across Belva Crater (Extreme Wall Incline >30 deg)
    run_mission_demo(
        name="EXPEDITION 2: Base Alpha -> Belva Crater North Outpost (Direct Cliff Traverse)",
        start=Coordinate(lat=18.380, lon=77.580),
        end=Coordinate(lat=18.480, lon=77.520),
        max_safe_slope=20.0
    )
