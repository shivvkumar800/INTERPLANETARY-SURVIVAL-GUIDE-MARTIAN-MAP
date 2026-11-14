"""
NASA Space Apps Challenge 2026: Interplanetary Survival Guide - Martian Map.
FastAPI Backend Application with CORS, Weighted A* Routing Engine, and Jezero Crater Terrain Hazards.
"""

import time
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import (
    RouteRequest,
    RouteResponse,
    TerrainGridResponse,
    TerrainBounds,
    WaypointPreset,
)
from terrain import (
    get_terrain,
    MIN_LAT,
    MAX_LAT,
    MIN_LON,
    MAX_LON,
)
from router import MartianRouter

app = FastAPI(
    title="Interplanetary Survival Guide: Martian Map Routing Engine",
    description="""
# 🚀 2026 NASA Space Apps Challenge: Jezero Crater Mission Survival Routing API

This high-performance backend calculates and benchmarks **Direct Trajectories** vs. **Weighted Safe Survival Paths** across Martian terrain in Jezero Crater (the landing site and exploration zone of NASA's *Perseverance* rover).

### Core Capabilities:
- **Topographic Terrain Modeling**: Accurate 2D elevation grid with physical slope gradient calculation (degrees), cosmic radiation exposure, and Séítah-like loose sand dune entrapment zones.
- **Direct Path Analysis**: Straight-line traversal evaluating elevation profile, steep incline penalties, and mission-critical hazard warnings.
- **8-Directional Weighted A* Routing Engine**: Intelligent detour planning that enforces strict slope limits (e.g., slopes > 20° are deemed impassable) and optimizes cost penalties across distance, slope steepness (10°–25°), radiation risk, and dust storm hazards.
- **EVA & Rover Transit Modeling**: Physical metric distances on the Martian ellipsoid with realistic Extravehicular Activity (EVA) traversal time estimations.
- **Interactive Terrain Heatmap API**: Exposes elevation, slope, radiation, and dust layers with configurable downsampling for frontend WebGL/Canvas rendering.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable Cross-Origin Resource Sharing (CORS) for frontend Web apps (React, Vue, Leaflet, Three.js)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize terrain and router singletons
terrain = get_terrain()
router = MartianRouter(terrain)


@app.get("/", tags=["System & Health"])
def root_info():
    """System information, active theater coordinates, and API navigation."""
    return {
        "mission": "NASA Space Apps Challenge 2026 - Interplanetary Survival Guide",
        "system": "Martian Map Weighted Safe-Path Routing Engine",
        "crater": "Jezero Crater, Mars (18.38 N, 77.58 E)",
        "docs_url": "/docs",
        "endpoints": {
            "route_calculate": "POST /api/route/calculate",
            "terrain_grid": "GET /api/terrain/grid",
            "health": "GET /api/health"
        },
        "sample_test_waypoint_alpha": {"lat": 18.380, "lon": 77.580, "name": "Base Alpha (Octavia Landing)"},
        "sample_test_waypoint_bravo": {"lat": 18.445, "lon": 77.455, "name": "Kodiak Butte (Western Delta)"}
    }


@app.get("/api/health", tags=["System & Health"])
def health_check():
    """Health check endpoint to verify backend operational readiness."""
    return {
        "status": "online",
        "grid_status": f"{terrain.rows}x{terrain.cols} grid loaded in memory",
        "crs": "Areocentric IAU 2000 Mars (R=3389.5km)"
    }


@app.get("/api/terrain/grid", response_model=TerrainGridResponse, tags=["Terrain & Environmental Hazards"])
def get_terrain_grid(
    downsample: int = Query(
        default=1,
        ge=1,
        le=4,
        description="Optional downsampling factor (1=100x100, 2=50x50, 4=25x25) for optimized frontend rendering"
    )
):
    """
    Returns 2D matrix arrays of elevation, slope, radiation, and dust hazards across Jezero Crater.
    Used by frontend mapping clients (Canvas/Leaflet/Deck.gl) to render colored hazard heatmaps.
    """
    step = downsample
    sampled_elevation = terrain.elevation[::step, ::step].tolist()
    sampled_slope = terrain.slope[::step, ::step].tolist()
    sampled_rad = terrain.radiation[::step, ::step].tolist()
    sampled_dust = terrain.dust[::step, ::step].tolist()

    rows = len(sampled_elevation)
    cols = len(sampled_elevation[0]) if rows > 0 else 0

    bounds = TerrainBounds(
        min_lat=terrain.min_lat,
        max_lat=terrain.max_lat,
        min_lon=terrain.min_lon,
        max_lon=terrain.max_lon,
        cell_width_m=round(terrain.dx_m * step, 1),
        cell_height_m=round(terrain.dy_m * step, 1)
    )

    presets = [WaypointPreset(**p) for p in terrain.get_presets()]

    return TerrainGridResponse(
        bounds=bounds,
        rows=rows,
        cols=cols,
        elevation=sampled_elevation,
        slope=sampled_slope,
        radiation=sampled_rad,
        dust=sampled_dust,
        presets=presets
    )


@app.post(
    "/api/route/calculate",
    response_model=RouteResponse,
    status_code=status.HTTP_200_OK,
    tags=["Routing Engine"]
)
def calculate_route(request: RouteRequest):
    """
    **Dual Routing Engine Endpoint**:
    Calculates and compares a **Direct Path** (sampling terrain without detour) against a **Safe Survival Path** (8-directional Weighted A* detour around steep slopes and radiation/dust zones).

    - **Inputs**:
      - `start`: {lat, lon} (Valid range: Lat 18.20-18.60, Lon 77.30-77.80)
      - `end`: {lat, lon}
      - `max_safe_slope`: Maximum traversable slope (default 20.0 deg)
      - `weights`: {distance, slope_penalty, hazard_penalty}
    - **Outputs**:
      - `direct_path`: Coordinates, distance, max slope, elevation/slope arrays, and hazard warnings.
      - `safe_survival_path`: Coordinates, distance, max slope, estimated EVA time, elevation/slope arrays, and detour %.
      - `comparison_summary`: Analytical briefing on hazards avoided and distance/time tradeoffs.
    """
    t0 = time.perf_counter()

    # Validate coordinate bounds
    for pt_name, pt in [("Start", request.start), ("End", request.end)]:
        if not (MIN_LAT <= pt.lat <= MAX_LAT and MIN_LON <= pt.lon <= MAX_LON):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY if hasattr(status, "HTTP_422_UNPROCESSABLE_ENTITY") else 422,
                detail=(
                    f"{pt_name} coordinate ({pt.lat}, {pt.lon}) is outside the Jezero Crater operational theater. "
                    f"Valid bounds: Latitude [{MIN_LAT}, {MAX_LAT}], Longitude [{MIN_LON}, {MAX_LON}]."
                )
            )

    response = router.route_mission(
        start=request.start,
        end=request.end,
        max_safe_slope=request.max_safe_slope,
        weights=request.weights
    )

    exec_time_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    response.metadata["execution_time_ms"] = exec_time_ms

    return response


if __name__ == "__main__":
    import uvicorn
    print("Launching Jezero Crater Survival Routing API on http://127.0.0.1:8000 ...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
