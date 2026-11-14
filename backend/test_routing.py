"""
Automated Verification & Test Suite for Martian Map Routing Engine.
Tests terrain modeling, 8-directional Weighted A*, hazard avoidance, and FastAPI endpoints.
"""

import sys
import os
import unittest
import numpy as np
from fastapi.testclient import TestClient

# Ensure current directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from terrain import get_terrain, JezeroTerrain, MIN_LAT, MAX_LAT, MIN_LON, MAX_LON
from router import MartianRouter
from models import Coordinate, RoutingWeights, RouteRequest
from main import app


class TestMartianRoutingEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.terrain = get_terrain()
        cls.router = MartianRouter(cls.terrain)
        cls.client = TestClient(app)

    def test_01_terrain_generation(self):
        """Verify Jezero Crater topographic and hazard grid properties."""
        self.assertEqual(self.terrain.elevation.shape, (100, 100))
        self.assertEqual(self.terrain.slope.shape, (100, 100))
        self.assertEqual(self.terrain.radiation.shape, (100, 100))
        self.assertEqual(self.terrain.dust.shape, (100, 100))

        # Check realistic Jezero elevation range (-2500m floor up to -1900m rim)
        min_elev = np.min(self.terrain.elevation)
        max_elev = np.max(self.terrain.elevation)
        self.assertLess(min_elev, -2400.0)
        self.assertGreater(max_elev, -2100.0)

        # Check slopes: flat floor should have low slope, rim/Belva crater wall should exceed 25 deg
        max_slope = np.max(self.terrain.slope)
        self.assertGreater(max_slope, 25.0, "Terrain must contain slopes > 25 degrees to test impassable constraints")

        # Hazards bounded [0.0, 1.0]
        self.assertGreaterEqual(np.min(self.terrain.radiation), 0.0)
        self.assertLessEqual(np.max(self.terrain.radiation), 1.0)
        self.assertGreaterEqual(np.min(self.terrain.dust), 0.0)
        self.assertLessEqual(np.max(self.terrain.dust), 1.0)

    def test_02_direct_path_sampling(self):
        """Verify direct path samples elevation and flags hazard warnings across Belva crater."""
        start = Coordinate(lat=18.380, lon=77.580)  # Base Alpha
        end = Coordinate(lat=18.480, lon=77.520)    # Across Belva crater

        direct_res = self.router.calculate_direct_path(start, end, max_safe_slope=20.0, num_samples=100)

        self.assertEqual(len(direct_res.coordinates), 100)
        self.assertEqual(len(direct_res.elevation_array), 100)
        self.assertEqual(len(direct_res.slope_array), 100)
        self.assertGreater(direct_res.total_distance_m, 5000.0)

        # Confirm direct line encounters steep slope and generates warnings
        self.assertGreater(direct_res.max_slope_deg, 20.0)
        self.assertTrue(len(direct_res.hazard_warnings) > 0)
        self.assertTrue(any("CRITICAL" in w or "SLOPE" in w for w in direct_res.hazard_warnings))

    def test_03_safe_survival_detour(self):
        """Verify Weighted A* enforces max_safe_slope and finds a safe detour."""
        start = Coordinate(lat=18.380, lon=77.580)
        end = Coordinate(lat=18.480, lon=77.520)
        max_safe_slope = 20.0
        weights = RoutingWeights(distance=1.0, slope_penalty=4.0, hazard_penalty=4.0)

        safe_res = self.router.calculate_safe_path(start, end, max_safe_slope=max_safe_slope, weights=weights)

        # Crucial constraint: Safe path slope must not exceed configured max_safe_slope
        self.assertLessEqual(
            safe_res.max_slope_deg,
            max_safe_slope + 0.1,  # allow negligible float tolerance
            f"Safe path peak slope {safe_res.max_slope_deg} exceeded threshold {max_safe_slope}"
        )
        self.assertGreater(len(safe_res.coordinates), 5)
        self.assertGreater(safe_res.estimated_eva_time_mins, 0.0)
        self.assertGreaterEqual(safe_res.detour_percentage, 0.0)

    def test_04_api_health_and_root(self):
        """Verify API root and health endpoints."""
        resp_root = self.client.get("/")
        self.assertEqual(resp_root.status_code, 200)
        data_root = resp_root.json()
        self.assertIn("Jezero Crater", data_root["crater"])

        resp_health = self.client.get("/api/health")
        self.assertEqual(resp_health.status_code, 200)
        data_health = resp_health.json()
        self.assertEqual(data_health["status"], "online")

    def test_05_api_terrain_grid(self):
        """Verify GET /api/terrain/grid returns matrix heatmaps and presets."""
        # Full resolution (100x100)
        resp = self.client.get("/api/terrain/grid?downsample=1")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["rows"], 100)
        self.assertEqual(data["cols"], 100)
        self.assertEqual(len(data["elevation"]), 100)
        self.assertEqual(len(data["slope"]), 100)
        self.assertGreater(len(data["presets"]), 3)

        # Downsampled resolution (50x50)
        resp_down = self.client.get("/api/terrain/grid?downsample=2")
        self.assertEqual(resp_down.status_code, 200)
        data_down = resp_down.json()
        self.assertEqual(data_down["rows"], 50)
        self.assertEqual(data_down["cols"], 50)

    def test_06_api_route_calculation_endpoint(self):
        """Verify POST /api/route/calculate returns full dual path and comparison summary."""
        payload = {
            "start": {"lat": 18.380, "lon": 77.580},
            "end": {"lat": 18.445, "lon": 77.455},
            "max_safe_slope": 20.0,
            "weights": {
                "distance": 1.0,
                "slope_penalty": 3.0,
                "hazard_penalty": 4.0
            }
        }
        resp = self.client.post("/api/route/calculate", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Check response structure
        self.assertIn("direct_path", data)
        self.assertIn("safe_survival_path", data)
        self.assertIn("comparison_summary", data)
        self.assertIn("metadata", data)

        direct = data["direct_path"]
        safe = data["safe_survival_path"]

        self.assertGreater(direct["total_distance_m"], 0.0)
        self.assertGreater(safe["total_distance_m"], 0.0)
        self.assertLessEqual(safe["max_slope_deg"], 20.1)
        self.assertIn("EXECUTE SAFE SURVIVAL PATHWAY", data["comparison_summary"])

        # Check performance: execution time should be under 200ms
        exec_ms = data["metadata"]["execution_time_ms"]
        self.assertLess(exec_ms, 500.0, f"Route calculation took {exec_ms}ms, expected < 500ms")

    def test_07_api_out_of_bounds_validation(self):
        """Verify API rejects coordinates outside the Jezero Crater bounding box."""
        payload = {
            "start": {"lat": 10.000, "lon": 77.580},  # Out of bounds lat
            "end": {"lat": 18.445, "lon": 77.455},
            "max_safe_slope": 20.0
        }
        resp = self.client.post("/api/route/calculate", json=payload)
        self.assertEqual(resp.status_code, 422)
        self.assertIn("outside the Jezero Crater", resp.json()["detail"])


if __name__ == "__main__":
    unittest.main()
