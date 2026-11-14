# 🚀 INTERPLANETARY SURVIVAL GUIDE: MARTIAN MAP
### NASA Space Apps Challenge 2026 // Surface Reconnaissance & Tactical EVA Navigation

[![NASA Space Apps Challenge 2026](https://img.shields.io/badge/NASA_Space_Apps-Challenge_2026-blue.svg)](https://www.spaceappschallenge.org/2026/challenges/interplanetary-survival-guide-martian-map/)
[![Mission](https://img.shields.io/badge/Mission-ARES_EVA--01-orange.svg)]()
[![Datum](https://img.shields.io/badge/Datum-IAU_2000_Mars_Sphere-red.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An intelligent, real-time surface reconnaissance and tactical survival navigation platform built for crewed Marswalk (EVA) surface exploration missions. Grounded in authentic **NASA planetary datasets**, **8-directional Weighted A\* pathfinding algorithms**, and multi-spectral orbital telemetry (**MOLA**, **THEMIS**, **CRISM**, **RAD**, **REMS**).

---

## 🛰️ 1. Mission Challenge & Scientific Objectives

Under NASA's **Interplanetary Survival Guide: Martian Map** challenge, astronauts navigating the unforgiving Martian regolith face severe environmental, geomechanical, and radiation threats. A direct line-of-sight traverse frequently crosses impassable crater scarps and loose sand dune fields that can trap rover wheels or cause unrecoverable EVA suit rollovers.

### Core Scientific & Exploration Goals
- **Jezero Crater Exploration**: Navigate from Ares Landing Base (`18.38° N, 77.58° E`) across the crater floor to cache biosignature samples at the ancient Neretva Vallis delta mudstones.
- **Curiosity 2025 Boxwork Formations**: Analyze the groundbreaking web-like boxwork mineral cement formations investigated by the Curiosity rover in 2025 at Mount Sharp (Gale Crater).
- **Hazard Scarp Avoidance**: Prevent vehicle rollover by enforcing a strict **15.0° slope limit** and avoiding the high-risk loose dune silt corridors of the Séítah formation.
- **ISRU Water Ice Prospecting**: Map pure subsurface water ice sheets (1.0–2.5 m depth) in Arcadia Planitia for crew hydration and rocket propellant production.

---

## ⚡ 2. Key Architecture & Features

### 🌌 A. Cinematic Entry & Inside-the-Helmet Visor POV
- **Pure Black Seamless Hero Layout**: Blends the astronaut helmet profile photo seamlessly with deep space black (`#000000`).
- **Luxury Editorial Aerospace Typography**: Powered by Google Fonts (`Syne`, `Syncopate`, `Space Grotesk`, `Rajdhani`).
- **Subtle Cosmic Backdrop**: Multi-layer dynamic starfield and shooting meteors.
- **Tap-to-Zoom Descent Transition**: Tapping anywhere initiates a hyper-zoom into the visor glass (`transform-origin: 78% 48%`), backed by Web Audio API airlock suction whooshes and harmonic entry chimes.
- **Martian Horizon Surround View**: Atmospheric red dust canvas with distant crater mountains, drifting sand particles, and sunlight glare.

### 🗺️ B. Tactical A* Route Analysis & Hazard Avoidance HUD
- **8-Directional Weighted A\* Solver**:
  - Grid Resolution: $239\text{ m} \times 283.5\text{ m}$
  - Mars Datum: Areocentric IAU 2000 Mars Sphere ($R = 3,389,500\text{ m}$)
  - Solver Runtime: $45.09\text{ ms}$
- **Direct Hazard Path (Red Dashed Line)**:
  - Total Distance: $8,403.9\text{ m}$ ($8.40\text{ km}$)
  - Peak Incline: **$19.14^\circ$** (Critical Cliff Scarp)
  - Hazard Verdict: **`NON-SURVIVABLE`** (Wheel entrapment in Séítah dune regolith & severe rollover risk).
- **Safe Survival Path (Cyan Glowing Solid Line)**:
  - Total Distance: $10,947.7\text{ m}$ ($10.95\text{ km}$)
  - Peak Incline: **$12.29^\circ$** (Well below the $20^\circ$ safe threshold)
  - Tradeoff: $+30.5\%$ Detour ($+2.54\text{ km}$)
  - Estimated EVA Traverse Duration: **$76.6\text{ minutes}$**
  - Hazard Verdict: **`100% CREW & ROVER SURVIVABILITY`**

### 🔬 C. Multi-Spectral NASA Sensor Layers
Astronauts can toggle multi-spectral orbital datasets directly on the tactical radar map:
1. **Topographic (MOLA)**: Mars Orbiter Laser Altimeter elevation contours and steep slope shading.
2. **Thermal Inertia (THEMIS)**: Nighttime infrared thermal inertia distinguishing hard bedrock from hazardous loose dune silt.
3. **Spectral Minerals (CRISM)**: Compact Reconnaissance Imaging Spectrometer mapping hydrated clay minerals, phyllosilicates, and carbonates in Jezero delta.
4. **Radiation Exposure (RAD)**: Cosmic ray surface dose contours across crater rims and unprotected plains.

### 🏃 D. Real-Time EVA Simulation Engine
Click **`SIMULATE EVA TRAVERSE`** (or press `[SPACE]`) to watch the astronaut traverse waypoints #1 through #37 with live updating HUD telemetry:
- Real-time Areocentric Latitude & Longitude
- Surface Elevation ($-2,494\text{ m}$ to $-2,415\text{ m}$)
- Local Slope Angle & Safety Classification
- Mission Progress Percentage
- Estimated Oxygen Reserve ($O_2$) Consumption
- Cumulative Distance Covered

### 📊 E. Interactive Terrain Cross-Section & Slope Profile
- High-DPI canvas plotting elevation from $-2,510\text{ m}$ to $-2,350\text{ m}$.
- Red dashed line highlighting the direct route's dangerous $19.14^\circ$ spike.
- $15^\circ$ vehicle rollover hazard threshold line.
- **Synchronized Hover Scrubbing**: Move your mouse across the elevation profile to view the corresponding coordinates and glowing waypoint reticle on the radar map in real-time.

---

## 📡 3. REST API Reference

The repository features two complementary components:
1. **Frontend Tactical Mission Control HUD** (`server.js` + `Mars Survival guide.html`)
2. **High-Performance Python Safe-Path Routing Engine** in [`/backend`](backend/) (`FastAPI` + `NumPy`)

### 🌐 Frontend Service (`server.js`)
| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/route-analysis` | `GET` | Returns the full 8-directional Weighted A* route analysis dataset with coordinates, elevations, and slopes. |
| `/api/mars-data` | `GET` | Returns environmental conditions (pressure, radiation, temperature, storm status) for all 6 exploration sites. |
| `/api/health` | `GET` | Returns microservice health, mission status (`ARES-2026`), and ISO timestamp. |
| `/` | `GET` | Serves the primary web application (`Mars Survival guide.html`). |

### 🚀 Python Safe-Path Routing Backend (`/backend`)
Built with **FastAPI** and **NumPy**, this engine provides real-time dual-path evaluation across Jezero Crater ($R_{\text{Mars}} = 3,389,500\text{ m}$ datum), calculating direct trajectories vs. 8-directional Weighted A* detours around steep slopes ($> 20.0^\circ$), cosmic radiation corridors, and Séítah dune entrapment fields.

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/route/calculate` | `POST` | Calculates & compares **Direct Path** vs **Safe Survival Path** with configurable slope limits and weights. |
| `/api/terrain/grid` | `GET` | Exposes 2D arrays of elevation, slope angles, radiation, and dust hazards with optional downsampling for heatmap rendering. |
| `/api/health` | `GET` | Backend system health and loaded terrain grid status. |
| `/docs` | `GET` | Interactive Swagger UI with pre-populated Jezero Crater test coordinates. |

#### `POST /api/route/calculate` Payload & Response:
```json
// Request Payload:
{
  "start": { "lat": 18.380, "lon": 77.580 },
  "end": { "lat": 18.445, "lon": 77.455 },
  "max_safe_slope": 20.0,
  "weights": { "distance": 1.0, "slope_penalty": 3.5, "hazard_penalty": 4.5 }
}

// Response Highlights:
{
  "direct_path": {
    "total_distance_m": 8011.3,
    "max_slope_deg": 14.08,
    "elevation_array": [...],
    "slope_array": [...],
    "hazard_warnings": ["CRITICAL ROLLOVER RISK...", "WHEEL ENTRAPMENT / DUST HAZARD..."]
  },
  "safe_survival_path": {
    "total_distance_m": 10751.6,
    "max_slope_deg": 12.29,
    "estimated_eva_time_mins": 75.5,
    "detour_percentage": 34.4
  },
  "comparison_summary": "MISSION ABORT PREVENTED: Direct trajectory is NON-SURVIVABLE due to extreme slopes... Safe Survival Path detoured around impassable crater scarps and Séítah sand dunes..."
}
```

---

## ⌨️ 4. Astronaut Flight Controls (Keyboard Shortcuts)

| Hotkey | Action |
| :---: | :--- |
| `[SPACE]` | Start / Pause Real-Time EVA Traverse Simulation |
| `[R]` | Reset EVA Simulation to Base Camp |
| `[1]` | Toggle Safe A* Survival Pathway |
| `[2]` | Toggle Direct Hazard Pathway |
| `[3]` | Compare Both Pathways Simultaneously |
| `[T]` | Open / Close Tactical Route Command Center |
| `[M]` | Toggle Synthesized Cosmic Audio & Equalizer |
| `[ESC]` | Close any active Holographic Dossier or Modal |

---

## 🛠️ 5. Quick Start & Local Execution

### Prerequisites
- Node.js (v18 or higher recommended)
- Python 3.10+ (for `/backend`)
- Any modern web browser (Chrome, Edge, Firefox, Safari)

### Option A: Run Python Safe-Path Routing Backend
```bash
# 1. Navigate to backend directory
cd backend

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch FastAPI backend
python run_server.py
# or: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
- **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Explorer**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Terrain Heatmap Grid**: [http://127.0.0.1:8000/api/terrain/grid](http://127.0.0.1:8000/api/terrain/grid)
- **Run Automated Tests**: `python test_routing.py`
- **Run CLI Demo**: `python demo_cli.py`

### Option B: Run Frontend Tactical Mission Control Server
```bash
# 1. Start Node.js Mission Control Server
node server.js
```
- **Web Application**: [http://localhost:8080](http://localhost:8080)
- **Route Analysis API**: [http://localhost:8080/api/route-analysis](http://localhost:8080/api/route-analysis)
- **Mars Environmental API**: [http://localhost:8080/api/mars-data](http://localhost:8080/api/mars-data)

---

## 🪐 6. Scientific Landing Zones Summary

| Site | Coordinates | Elevation | Primary Scientific Objective | Hazard Profile |
| :--- | :---: | :---: | :--- | :--- |
| **Jezero Crater** | $18.38^\circ\text{ N}, 77.58^\circ\text{ E}$ | $-2,560\text{ m}$ | Neretva delta mudstone biosignatures & MSR caching | Steep delta scarps ($28^\circ$), Séítah dunes |
| **Gale Crater (Mount Sharp)** | $-5.40^\circ\text{ S}, 137.8^\circ\text{ E}$ | $-4,450\text{ m}$ | Breakthrough 2025 Boxwork groundwater veins | Sharp ventifacts & steep gullies |
| **Ares Vallis** | $19.30^\circ\text{ N}, 33.50^\circ\text{ W}$ | $-3,680\text{ m}$ | Historic Pathfinder megaflood highland gravels | High boulder density ($>35\%$) |
| **Chryse Planitia** | $22.50^\circ\text{ N}, 48.00^\circ\text{ W}$ | $-3,900\text{ m}$ | Viking 1 volcanic plain & atmospheric baseline | Seasonal dust accumulation |
| **Valles Marineris** | $-14.0^\circ\text{ S}, 59.20^\circ\text{ W}$ | $-7,000\text{ m}$ | 4,000 km grand rift canyon layered bedrock strata | Sheer $7\text{ km}$ vertical drop-offs |
| **Arcadia Planitia** | $39.20^\circ\text{ N}, 189.7^\circ\text{ E}$ | $-4,100\text{ m}$ | Pure radar-mapped subsurface water ice sheets | Cryogenic frost-heave voids |

---

## 📜 7. License

Developed for the **NASA Space Apps Challenge 2026**. Open source under the [MIT License](LICENSE).
