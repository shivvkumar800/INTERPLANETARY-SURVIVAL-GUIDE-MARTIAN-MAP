# 🚀 Interplanetary Survival Guide: Martian Map Routing Engine
### 2026 NASA Space Apps Challenge — Jezero Crater Expedition Theater

A high-performance Python backend built with **FastAPI** and **NumPy** that calculates and benchmarks a **Direct Trajectory** vs. a **Weighted Safe Survival Path** across realistic Martian terrain in **Jezero Crater** (18.38° N, 77.58° E), the landing site and operational theater of NASA's *Perseverance* rover.

---

## 🌟 Architecture & Key Features

### 1. Dual Routing Engine
- **Direct Path**: Straight-line vector interpolation across the Martian sphere. Samples continuous elevation and slope profiles regardless of terrain hazards, accurately detecting rollover risks, sheer cliffs, and loose sand traps.
- **Safe Survival Path**: 8-directional **Weighted A* (A-Star)** pathfinding algorithm:
  - **Hard Constraints**: Slopes exceeding `max_safe_slope` (default 20.0° to 25.0°) or unconsolidated sand dune traps (dust index > 0.90) are strictly treated as impassable obstacles ($Cost = \infty$).
  - **Configurable Cost Penalties**: Applies non-linear cost multipliers for moderate slopes (10°–25°), cosmic radiation / Solar Particle Event (SPE) fluxes, and aeolian dust storm / wheel-slip zones.
  - **Admissible Heuristic**: 3D Euclidean distance to goal multiplied by the distance weight, guaranteeing optimal or near-optimal detour calculation in **sub-20 milliseconds**.
  - **EVA Transit Time Model**: Realistic Extravehicular Activity (EVA) time estimation based on rover nominal velocity ($10\text{ km/h} \approx 2.78\text{ m/s}$), penalized dynamically by slope angle cosine degradation and ground cohesion drag.

### 2. High-Fidelity Jezero Crater Terrain Model (`terrain.py`)
- **Spatial Bounds**: Latitude 18.20° N to 18.60° N, Longitude 77.30° E to 77.80° E ($23.6\text{ km} \times 28.1\text{ km}$).
- **Datum Elevation**: -2500m base crater basin rising to -1950m on the crater rim.
- **Physical Features Modeled**:
  - **Jezero Rim Crest**: Uplifted boundary with inner and outer wall slopes exceeding 28°–34°.
  - **Western River Delta (Neretva Vallis breach)**: Elevated alluvial fan (-2380m) with delta scarps (14°–22°).
  - **Belva Crater**: Secondary impact crater ($1.2\text{ km}$ across, $160\text{ m}$ depth) with steep crater walls exceeding 30° (acts as an impassable barrier on the crater floor).
  - **Kodiak Butte**: Isolated remnant mesa with layered delta bottomsets.
  - **Séítah Dune Field**: Loose drift sand and ripples posing high rover wheel entrapment risk.
  - **Cosmic Radiation / SPE Corridor**: High-exposure ridge crests and mineral anomaly zones.

---

## 📁 Project Structure

```text
martian_survival_backend/
├── main.py              # FastAPI app, CORS middleware, API endpoints, Swagger docs
├── models.py            # Pydantic v2 schemas, validation, sample payloads
├── terrain.py           # 2D Jezero Crater grid generator (elevation, slope, radiation, dust)
├── router.py            # Direct line sampler and 8-directional Weighted A* solver
├── demo_cli.py          # Interactive CLI showcasing mission simulations
├── test_routing.py      # Automated test suite (unit tests, API tests, benchmarks)
├── run_server.py        # Development server launcher (Uvicorn)
└── requirements.txt     # Python dependencies
```

---

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch Development Server
```bash
python run_server.py
# or
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Server endpoints will be active at:
- **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Explorer**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **API Health Check**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

### 3. Run Automated Tests
```bash
python test_routing.py
```
*Executes all 7 unit and integration tests in under 100 milliseconds.*

### 4. Run CLI Demonstration
```bash
python demo_cli.py
```

---

## 📡 API Reference

### 1. Calculate Route (`POST /api/route/calculate`)

#### Request Body
```json
{
  "start": { "lat": 18.380, "lon": 77.580 },
  "end": { "lat": 18.445, "lon": 77.455 },
  "max_safe_slope": 20.0,
  "weights": {
    "distance": 1.0,
    "slope_penalty": 3.5,
    "hazard_penalty": 4.5
  }
}
```

#### Response Example
```json
{
  "direct_path": {
    "coordinates": [
      { "lat": 18.38, "lon": 77.58 },
      { "lat": 18.38066, "lon": 77.57874 }
    ],
    "total_distance_m": 8011.3,
    "max_slope_deg": 14.08,
    "elevation_array": [-2493.6, -2494.1],
    "slope_array": [2.1, 2.4],
    "hazard_warnings": [
      "VERDICT: DIRECT PATH CLASSIFIED AS NON-SURVIVABLE FOR CREWED EVA / UNPROTECTED ROVER.",
      "WHEEL ENTRAPMENT / DUST HAZARD: Direct line traverses 39% of journey inside high-risk loose dune regolith (Séítah/Delta silt zones). Extreme risk of rover entrapment and solar panel fouling."
    ]
  },
  "safe_survival_path": {
    "coordinates": [
      { "lat": 18.38, "lon": 77.58 },
      { "lat": 18.38202, "lon": 77.57747 }
    ],
    "total_distance_m": 10751.6,
    "max_slope_deg": 12.29,
    "estimated_eva_time_mins": 75.5,
    "elevation_array": [-2493.6, -2491.2],
    "slope_array": [2.1, 3.4],
    "detour_percentage": 34.4
  },
  "comparison_summary": "MISSION ABORT PREVENTED: Direct trajectory is NON-SURVIVABLE due to extreme slopes (peak 14.1 deg) and hazardous regolith corridors. The Safe Survival Path detoured around impassable crater scarps and Séítah sand dunes, limiting peak incline to 12.3 deg. Tradeoff: Detour adds 2.74 km (+34.4%) and requires an estimated 75.5 minutes of EVA traverse time to guarantee 100% crew and rover survival. OPERATIONAL VERDICT: EXECUTE SAFE SURVIVAL PATHWAY.",
  "metadata": {
    "region": "Jezero Crater, Mars",
    "crs": "Areocentric IAU 2000 Mars Sphere (R=3,389,500m)",
    "grid_resolution_m": { "dy": 239.0, "dx": 283.5 },
    "solver": "8-directional Weighted A* (Admissible Euclidean Heuristic)",
    "safe_max_slope_enforced": 20.0,
    "execution_time_ms": 15.42
  }
}
```

---

### 2. Retrieve Terrain Grid (`GET /api/terrain/grid`)

#### Query Parameters:
- `downsample`: Integer `1` to `4` (default `1`).
  - `1`: Full $100 \times 100$ grid ($10,000$ cells).
  - `2`: Optimized $50 \times 50$ grid ($2,500$ cells) for high-FPS frontend HTML5 Canvas / Leaflet heatmap overlays.

#### Response Example
```json
{
  "bounds": {
    "min_lat": 18.2,
    "max_lat": 18.6,
    "min_lon": 77.3,
    "max_lon": 77.8,
    "cell_width_m": 567.0,
    "cell_height_m": 478.0,
    "mars_mean_radius_m": 3389500.0
  },
  "rows": 50,
  "cols": 50,
  "elevation": [[-2315.4, -2318.2]],
  "slope": [[8.4, 7.9]],
  "radiation": [[0.35, 0.38]],
  "dust": [[0.12, 0.15]],
  "presets": [
    {
      "id": "base_alpha",
      "name": "Octavia E. Butler Landing (Base Alpha)",
      "description": "Perseverance rover landing site on smooth Jezero Crater floor.",
      "coordinate": { "lat": 18.38, "lon": 77.58 },
      "feature_type": "Expedition Base"
    },
    {
      "id": "kodiak_butte",
      "name": "Kodiak Butte Delta Overlook",
      "description": "Prominent isolated remnant mesa exposing ancient delta bottomset and foreset strata.",
      "coordinate": { "lat": 18.445, "lon": 77.455 },
      "feature_type": "Scientific Target"
    }
  ]
}
```

---

## 🧪 Scientific Validation & Coordinates Reference

| Waypoint | Latitude | Longitude | Description |
|---|---|---|---|
| **Base Alpha** | 18.380° N | 77.580° E | Perseverance Octavia E. Butler Landing site |
| **Kodiak Butte** | 18.445° N | 77.455° E | Western Delta front overlook |
| **Belva Crater Rim** | 18.480° N | 77.520° E | Steep secondary crater wall (>32° slope) |
| **Neretva Vallis** | 18.410° N | 77.360° E | Ancient river canyon rim breach |
| **Séítah Station** | 18.365° N | 77.535° E | Loose sand dunes & wheel-slip hazard |
| **Eastern Rim** | 18.350° N | 77.720° E | High-elevation ridge & cosmic ray flux |

---

## 🛡️ License
Built for the NASA Space Apps Challenge 2026. Open-source under MIT License.
