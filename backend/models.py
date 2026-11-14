"""
Pydantic Schemas for Martian Map Weighted Safe-Path Routing Engine.
NASA Space Apps Challenge: Interplanetary Survival Guide - Jezero Crater, Mars.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Coordinate(BaseModel):
    """Areocentric Martian coordinates in degrees."""
    lat: float = Field(..., description="Martian latitude in degrees North (18.20 to 18.60 for Jezero region)")
    lon: float = Field(..., description="Martian longitude in degrees East (77.30 to 77.80 for Jezero region)")

    model_config = {
        "json_schema_extra": {
            "example": {"lat": 18.380, "lon": 77.580}
        }
    }


class RoutingWeights(BaseModel):
    """Configurable cost multiplier weights for the survival pathfinding engine."""
    distance: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Weight factor for ground distance traveled (meters)"
    )
    slope_penalty: float = Field(
        default=3.0,
        ge=0.0,
        le=20.0,
        description="Penalty multiplier for slopes between 10 deg and max_safe_slope"
    )
    hazard_penalty: float = Field(
        default=4.0,
        ge=0.0,
        le=20.0,
        description="Penalty multiplier for cosmic radiation and dust storm / dune entrapment risks"
    )


class RouteRequest(BaseModel):
    """Input payload for POST /api/route/calculate."""
    start: Coordinate = Field(
        ...,
        description="Expedition starting coordinates (e.g., Octavia E. Butler Landing / Jezero Floor Base)"
    )
    end: Coordinate = Field(
        ...,
        description="Expedition destination coordinates (e.g., Western Delta Kodiak Butte or Belva Rim)"
    )
    max_safe_slope: float = Field(
        default=20.0,
        ge=5.0,
        le=35.0,
        description="Maximum traversable slope angle in degrees. Slopes above this threshold are deemed impassable."
    )
    weights: RoutingWeights = Field(
        default_factory=RoutingWeights,
        description="Cost weights for path optimization"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "start": {"lat": 18.380, "lon": 77.580},
                    "end": {"lat": 18.450, "lon": 77.450},
                    "max_safe_slope": 20.0,
                    "weights": {
                        "distance": 1.0,
                        "slope_penalty": 3.5,
                        "hazard_penalty": 4.5
                    }
                },
                {
                    "start": {"lat": 18.350, "lon": 77.620},
                    "end": {"lat": 18.420, "lon": 77.500},
                    "max_safe_slope": 18.0,
                    "weights": {
                        "distance": 1.0,
                        "slope_penalty": 4.0,
                        "hazard_penalty": 5.0
                    }
                }
            ]
        }
    }


class DirectPathResult(BaseModel):
    """Direct straight-line interpolated path metrics regardless of terrain dangers."""
    coordinates: List[Coordinate] = Field(..., description="Series of interpolated coordinates along direct line")
    total_distance_m: float = Field(..., description="Total 3D Euclidean traversal distance in meters")
    max_slope_deg: float = Field(..., description="Maximum slope angle encountered along direct line (degrees)")
    elevation_array: List[float] = Field(..., description="Array of elevation values in meters along direct line")
    slope_array: List[float] = Field(..., description="Array of slope angles in degrees along direct line")
    hazard_warnings: List[str] = Field(..., description="List of mission-critical safety warnings identified on direct line")


class SafePathResult(BaseModel):
    """Optimized detour path avoiding impassable terrain, steep inclines, and hazard zones."""
    coordinates: List[Coordinate] = Field(..., description="Series of waypoint coordinates along calculated safe route")
    total_distance_m: float = Field(..., description="Total 3D traversal distance in meters of safe detour")
    max_slope_deg: float = Field(..., description="Maximum slope angle encountered along safe path (degrees)")
    estimated_eva_time_mins: float = Field(..., description="Estimated Extravehicular Activity travel time in minutes")
    elevation_array: List[float] = Field(..., description="Array of elevation values in meters along safe path")
    slope_array: List[float] = Field(..., description="Array of slope angles in degrees along safe path")
    detour_percentage: float = Field(..., description="Percentage of extra distance compared to direct path")


class RouteResponse(BaseModel):
    """Complete response payload for POST /api/route/calculate."""
    direct_path: DirectPathResult
    safe_survival_path: SafePathResult
    comparison_summary: str = Field(..., description="Executive survival summary comparing hazards and route tradeoff")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution metrics, Mars coordinate datum, and solver info")


class TerrainBounds(BaseModel):
    """Bounding box and spatial resolution of Jezero Crater terrain grid."""
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float
    cell_width_m: float
    cell_height_m: float
    mars_mean_radius_m: float = 3389500.0


class WaypointPreset(BaseModel):
    """Predefined landmarks and scientific investigation sites in Jezero Crater."""
    id: str
    name: str
    description: str
    coordinate: Coordinate
    feature_type: str


class TerrainGridResponse(BaseModel):
    """Response payload for GET /api/terrain/grid to power frontend heatmaps and overlays."""
    bounds: TerrainBounds
    rows: int
    cols: int
    elevation: List[List[float]] = Field(..., description="2D grid of elevations in meters (datum -2500m base)")
    slope: List[List[float]] = Field(..., description="2D grid of slope angles in degrees")
    radiation: List[List[float]] = Field(..., description="2D grid of normalized cosmic/SPE radiation risk (0.0 to 1.0)")
    dust: List[List[float]] = Field(..., description="2D grid of normalized dust storm / sand dune trap risk (0.0 to 1.0)")
    presets: List[WaypointPreset] = Field(..., description="Sample waypoints for interactive testing and demonstration")
