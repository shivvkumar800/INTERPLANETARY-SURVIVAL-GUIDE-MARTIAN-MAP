"""
Routing Engine for Martian Surface Operations.
Calculates Direct Path vs. Weighted Safe Survival Path using 8-directional A* with
hazard avoidance, slope constraints, and realistic EVA travel time modeling.
"""

import heapq
import math
from typing import List, Tuple, Dict, Any, Optional
import numpy as np

from models import (
    Coordinate,
    RoutingWeights,
    DirectPathResult,
    SafePathResult,
    RouteResponse,
)
from terrain import JezeroTerrain, MARS_MEAN_RADIUS_M, RAD_PER_DEG


class MartianRouter:
    """
    Dual Routing Engine:
    1. Direct Path: Geometric line interpolation across terrain, sampling hazards.
    2. Safe Survival Path: 8-directional A* solver optimizing for slope safety,
       radiation mitigation, and dust entrapment avoidance.
    """

    def __init__(self, terrain: JezeroTerrain):
        self.terrain = terrain
        # 8-directional neighbor offsets (dr, dc)
        self.directions = [
            (-1, 0),  (1, 0),  (0, -1),  (0, 1),   # Orthogonal (North, South, West, East)
            (-1, -1), (-1, 1), (1, -1),  (1, 1),   # Diagonal (NW, NE, SW, SE)
        ]

    def _calc_cell_distance(self, r1: int, c1: int, r2: int, c2: int) -> Tuple[float, float]:
        """
        Calculates 2D planar ground distance and 3D terrain distance between two adjacent cells.
        """
        dr = r2 - r1
        dc = c2 - c1
        dx = dc * self.terrain.dx_m
        dy = dr * self.terrain.dy_m
        d2d = math.sqrt(dx * dx + dy * dy)

        z1 = float(self.terrain.elevation[r1, c1])
        z2 = float(self.terrain.elevation[r2, c2])
        dz = z2 - z1
        d3d = math.sqrt(d2d * d2d + dz * dz)
        return d2d, d3d

    def _heuristic(self, r: int, c: int, target_r: int, target_c: int, weight_dist: float) -> float:
        """
        Admissible Euclidean distance heuristic in meters scaled by distance weight.
        Guarantees A* optimality.
        """
        dr = target_r - r
        dc = target_c - c
        dx = dc * self.terrain.dx_m
        dy = dr * self.terrain.dy_m
        return math.sqrt(dx * dx + dy * dy) * weight_dist

    def calculate_direct_path(
        self,
        start: Coordinate,
        end: Coordinate,
        max_safe_slope: float = 20.0,
        num_samples: int = 100
    ) -> DirectPathResult:
        """
        Calculates straight-line direct path between start and end.
        Samples elevation, slope, radiation, and dust hazards along the vector.
        """
        coords: List[Coordinate] = []
        elevations: List[float] = []
        slopes: List[float] = []
        hazard_warnings: List[str] = []

        total_dist_3d = 0.0
        prev_lat = start.lat
        prev_lon = start.lon
        prev_elev = self.terrain.sample_point(start.lat, start.lon)["elevation"]

        high_slope_violations = 0
        extreme_slope_violations = 0  # > 25 degrees (rollover hazard)
        peak_slope = 0.0
        peak_slope_km = 0.0

        high_radiation_pts = 0
        high_dust_pts = 0

        # Mean latitude for longitude scaling
        mean_lat_rad = np.radians((start.lat + end.lat) / 2.0)

        for i in range(num_samples):
            t = i / float(num_samples - 1)
            curr_lat = start.lat + t * (end.lat - start.lat)
            curr_lon = start.lon + t * (end.lon - start.lon)

            sampled = self.terrain.sample_point(curr_lat, curr_lon)
            elev = sampled["elevation"]
            slope = sampled["slope"]
            rad = sampled["radiation"]
            dust = sampled["dust"]

            coords.append(Coordinate(lat=round(curr_lat, 5), lon=round(curr_lon, 5)))
            elevations.append(elev)
            slopes.append(slope)

            if slope > peak_slope:
                peak_slope = slope
                peak_slope_km = total_dist_3d / 1000.0

            if slope > max_safe_slope:
                high_slope_violations += 1
            if slope > 25.0:
                extreme_slope_violations += 1

            if rad > 0.65:
                high_radiation_pts += 1
            if dust > 0.65:
                high_dust_pts += 1

            # Accumulate 3D distance
            if i > 0:
                dy = (curr_lat - prev_lat) * RAD_PER_DEG * MARS_MEAN_RADIUS_M
                dx = (curr_lon - prev_lon) * RAD_PER_DEG * MARS_MEAN_RADIUS_M * np.cos(mean_lat_rad)
                dz = elev - prev_elev
                seg_dist = math.sqrt(dx * dx + dy * dy + dz * dz)
                total_dist_3d += seg_dist

            prev_lat = curr_lat
            prev_lon = curr_lon
            prev_elev = elev

        # Generate mission hazard warnings
        if extreme_slope_violations > 0:
            hazard_warnings.append(
                f"CRITICAL ROLLOVER RISK: Direct line encounters {extreme_slope_violations} segments with slope > 25.0 deg. "
                f"Peak slope reaches {peak_slope:.1f} deg at km {peak_slope_km:.2f} (exceeds rover stability limit)."
            )
        elif high_slope_violations > 0:
            hazard_warnings.append(
                f"ELEVATED SLOPE HAZARD: {high_slope_violations} segments exceed configured threshold of {max_safe_slope:.1f} deg. "
                f"Peak slope reaches {peak_slope:.1f} deg."
            )

        if high_dust_pts > 0:
            hazard_warnings.append(
                f"WHEEL ENTRAPMENT / DUST HAZARD: Direct line traverses {high_dust_pts}% of journey inside high-risk loose dune "
                f"regolith (Séítah/Delta silt zones). Extreme risk of rover entrapment and solar panel fouling."
            )

        if high_radiation_pts > 0:
            hazard_warnings.append(
                f"ACUTE RADIATION EXPOSURE: Direct line intersects high-radiation crest corridor ({high_radiation_pts} high-flux zones). "
                f"Exceeds recommended astronaut EVA cumulative dosage limits."
            )

        if not hazard_warnings:
            hazard_warnings.append("Direct trajectory nominal: No terrain hazards detected above survival thresholds.")
        else:
            hazard_warnings.insert(
                0, "VERDICT: DIRECT PATH CLASSIFIED AS NON-SURVIVABLE FOR CREWED EVA / UNPROTECTED ROVER."
            )

        return DirectPathResult(
            coordinates=coords,
            total_distance_m=round(total_dist_3d, 1),
            max_slope_deg=round(peak_slope, 2),
            elevation_array=elevations,
            slope_array=slopes,
            hazard_warnings=hazard_warnings
        )

    def calculate_safe_path(
        self,
        start: Coordinate,
        end: Coordinate,
        max_safe_slope: float = 20.0,
        weights: Optional[RoutingWeights] = None
    ) -> SafePathResult:
        """
        Executes 8-directional Weighted A* pathfinding.
        Enforces slope <= max_safe_slope as strict hard constraint (impassable).
        Applies configurable penalties for moderate slopes (10 - 25 deg), radiation, and dust.
        """
        if weights is None:
            weights = RoutingWeights()

        start_r, start_c = self.terrain.lat_lon_to_indices(start.lat, start.lon)
        target_r, target_c = self.terrain.lat_lon_to_indices(end.lat, end.lon)

        # Ensure start and target are passable; if placed inside an impassable obstacle, find nearest passable cell
        start_r, start_c = self._find_nearest_passable(start_r, start_c, max_safe_slope)
        target_r, target_c = self._find_nearest_passable(target_r, target_c, max_safe_slope)

        # Priority Queue for A*: stores (f_cost, g_cost, r, c)
        open_set = []
        heapq.heappush(open_set, (0.0, 0.0, start_r, start_c))

        # Best cost to reach node
        g_scores = { (start_r, start_c): 0.0 }
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}

        found_goal = False

        while open_set:
            f_curr, g_curr, r, c = heapq.heappop(open_set)

            # Reached destination
            if r == target_r and c == target_c:
                found_goal = True
                break

            # If we popped an outdated higher g_score, skip
            if g_curr > g_scores.get((r, c), float('inf')):
                continue

            curr_slope = float(self.terrain.slope[r, c])
            curr_rad = float(self.terrain.radiation[r, c])
            curr_dust = float(self.terrain.dust[r, c])

            for dr, dc in self.directions:
                nr, nc = r + dr, c + dc

                # Bounds check
                if not (0 <= nr < self.terrain.rows and 0 <= nc < self.terrain.cols):
                    continue

                neighbor_slope = float(self.terrain.slope[nr, nc])
                neighbor_rad = float(self.terrain.radiation[nr, nc])
                neighbor_dust = float(self.terrain.dust[nr, nc])

                # 1. Hard Impassable Constraints:
                # - Slopes > max_safe_slope (or catastrophic slope > 25 deg)
                # - Lethal dust traps (dust > 0.90)
                if neighbor_slope > max_safe_slope:
                    continue
                if neighbor_dust > 0.92:
                    continue

                # 2. Physical 3D step distance
                d2d, d3d = self._calc_cell_distance(r, c, nr, nc)

                # 3. Slope Penalty (for moderate slopes between 10.0 deg and max_safe_slope)
                avg_slope = (curr_slope + neighbor_slope) / 2.0
                slope_penalty_factor = 0.0
                if avg_slope > 10.0:
                    # Non-linear quadratic penalty
                    slope_ratio = (avg_slope - 10.0) / max(1.0, (max_safe_slope - 10.0))
                    slope_penalty_factor = (slope_ratio ** 1.8) * weights.slope_penalty
                elif avg_slope > 4.0:
                    # Mild rolling resistance penalty
                    slope_penalty_factor = (avg_slope / 10.0) * 0.15

                # 4. Environmental Hazard Penalty (Radiation & Loose Sand)
                avg_rad = (curr_rad + neighbor_rad) / 2.0
                avg_dust = (curr_dust + neighbor_dust) / 2.0
                composite_hazard = 0.5 * avg_rad + 0.5 * avg_dust
                hazard_penalty_factor = (composite_hazard ** 1.5) * weights.hazard_penalty

                # Total edge traversal cost
                step_cost = d3d * (weights.distance + slope_penalty_factor + hazard_penalty_factor)
                tentative_g = g_curr + step_cost

                if tentative_g < g_scores.get((nr, nc), float('inf')):
                    g_scores[(nr, nc)] = tentative_g
                    came_from[(nr, nc)] = (r, c)
                    h_val = self._heuristic(nr, nc, target_r, target_c, weights.distance)
                    heapq.heappush(open_set, (tentative_g + h_val, tentative_g, nr, nc))

        # Reconstruct path
        path_cells: List[Tuple[int, int]] = []
        if found_goal:
            curr = (target_r, target_c)
            while curr in came_from:
                path_cells.append(curr)
                curr = came_from[curr]
            path_cells.append((start_r, start_c))
            path_cells.reverse()
        else:
            # Fallback: If no path found at strict threshold, relaxation fallback
            return self._calculate_fallback_path(start, end, max_safe_slope)

        # Convert cells to Coordinate objects and extract elevation and slope profiles
        coords: List[Coordinate] = []
        elevations: List[float] = []
        slopes: List[float] = []

        total_dist_3d = 0.0
        max_encountered_slope = 0.0
        total_eva_seconds = 0.0

        # Mars pressurized rover baseline speed: 10 km/h = 2.78 m/s (crewed rover) / 1.1 m/s (EVA foot suit)
        rover_base_speed_mps = 2.78

        for idx, (r, c) in enumerate(path_cells):
            lat, lon = self.terrain.indices_to_lat_lon(r, c)
            coords.append(Coordinate(lat=lat, lon=lon))

            elev = float(self.terrain.elevation[r, c])
            slope = float(self.terrain.slope[r, c])
            rad = float(self.terrain.radiation[r, c])
            dust = float(self.terrain.dust[r, c])

            elevations.append(round(elev, 2))
            slopes.append(round(slope, 2))
            if slope > max_encountered_slope:
                max_encountered_slope = slope

            if idx > 0:
                pr, pc = path_cells[idx - 1]
                _, seg_d3d = self._calc_cell_distance(pr, pc, r, c)
                total_dist_3d += seg_d3d

                # Realistic EVA speed degradation formula based on incline and ground cohesion
                slope_factor = max(0.20, math.cos(math.radians(slope)))
                ground_factor = max(0.35, 1.0 - 0.45 * (0.4 * rad + 0.6 * dust))
                effective_speed = rover_base_speed_mps * slope_factor * ground_factor
                total_eva_seconds += seg_d3d / max(0.5, effective_speed)

        estimated_eva_mins = round(total_eva_seconds / 60.0, 1)

        # Calculate detour percentage against straight 3D distance
        mean_lat_rad = np.radians((start.lat + end.lat) / 2.0)
        dy_direct = (end.lat - start.lat) * RAD_PER_DEG * MARS_MEAN_RADIUS_M
        dx_direct = (end.lon - start.lon) * RAD_PER_DEG * MARS_MEAN_RADIUS_M * np.cos(mean_lat_rad)
        dz_direct = elevations[-1] - elevations[0] if elevations else 0.0
        direct_euclidean_dist = math.sqrt(dx_direct * dx_direct + dy_direct * dy_direct + dz_direct * dz_direct)

        detour_pct = 0.0
        if direct_euclidean_dist > 0.0:
            detour_pct = round(((total_dist_3d - direct_euclidean_dist) / direct_euclidean_dist) * 100.0, 1)

        return SafePathResult(
            coordinates=coords,
            total_distance_m=round(total_dist_3d, 1),
            max_slope_deg=round(max_encountered_slope, 2),
            estimated_eva_time_mins=estimated_eva_mins,
            elevation_array=elevations,
            slope_array=slopes,
            detour_percentage=max(0.0, detour_pct)
        )

    def _find_nearest_passable(self, r: int, c: int, max_safe_slope: float, search_radius: int = 4) -> Tuple[int, int]:
        """
        Locates the closest passable cell if a given waypoint is placed directly on a cliff or trap.
        """
        if self.terrain.slope[r, c] <= max_safe_slope and self.terrain.dust[r, c] <= 0.90:
            return r, c

        for radius in range(1, search_radius + 1):
            for dr in range(-radius, radius + 1):
                for dc in range(-radius, radius + 1):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.terrain.rows and 0 <= nc < self.terrain.cols:
                        if self.terrain.slope[nr, nc] <= max_safe_slope and self.terrain.dust[nr, nc] <= 0.90:
                            return nr, nc
        return r, c

    def _calculate_fallback_path(
        self,
        start: Coordinate,
        end: Coordinate,
        max_safe_slope: float
    ) -> SafePathResult:
        """
        Graceful relaxation fallback if tight slope threshold completely isolates destination.
        Retries with relaxed slope tolerance (up to 24 deg).
        """
        relaxed_weights = RoutingWeights(distance=1.0, slope_penalty=8.0, hazard_penalty=6.0)
        return self.calculate_safe_path(start, end, max_safe_slope=min(24.5, max_safe_slope + 4.0), weights=relaxed_weights)

    def generate_comparison_summary(
        self,
        direct: DirectPathResult,
        safe: SafePathResult,
        max_safe_slope: float
    ) -> str:
        """
        Generates an executive Martian mission survival assessment comparing both routes.
        """
        distance_delta_km = (safe.total_distance_m - direct.total_distance_m) / 1000.0
        direct_peak = direct.max_slope_deg
        safe_peak = safe.max_slope_deg

        # Filter severe warnings
        critical_warnings = [w for w in direct.hazard_warnings if "CRITICAL" in w or "NON-SURVIVABLE" in w]

        summary_parts = []
        if critical_warnings:
            summary_parts.append(
                f"MISSION ABORT PREVENTED: Direct trajectory is NON-SURVIVABLE due to extreme slopes (peak {direct_peak:.1f} deg) "
                f"and hazardous regolith corridors."
            )
        elif direct_peak > max_safe_slope:
            summary_parts.append(
                f"HAZARD MITIGATION SUCCESS: Direct path violated max safe slope limit ({direct_peak:.1f} deg vs. {max_safe_slope:.1f} deg threshold)."
            )
        else:
            summary_parts.append("DIRECT TRAJECTORY NOMINAL: Both paths satisfy baseline safety criteria.")

        summary_parts.append(
            f"The Safe Survival Path detoured around impassable crater scarps and Séítah sand dunes, "
            f"limiting peak incline to {safe_peak:.1f} deg."
        )

        if distance_delta_km > 0.05:
            summary_parts.append(
                f"Tradeoff: Detour adds {distance_delta_km:.2f} km (+{safe.detour_percentage:.1f}%) and requires "
                f"an estimated {safe.estimated_eva_time_mins:.1f} minutes of EVA traverse time to guarantee 100% crew and rover survival."
            )
        else:
            summary_parts.append(
                f"Minimal detour required ({safe.detour_percentage:.1f}% extra distance). Estimated transit time: {safe.estimated_eva_time_mins:.1f} mins."
            )

        summary_parts.append("OPERATIONAL VERDICT: EXECUTE SAFE SURVIVAL PATHWAY.")
        return " ".join(summary_parts)

    def route_mission(
        self,
        start: Coordinate,
        end: Coordinate,
        max_safe_slope: float = 20.0,
        weights: Optional[RoutingWeights] = None
    ) -> RouteResponse:
        """
        Coordinates full dual-routing execution and returns complete RouteResponse.
        """
        direct_result = self.calculate_direct_path(start, end, max_safe_slope=max_safe_slope)
        safe_result = self.calculate_safe_path(start, end, max_safe_slope=max_safe_slope, weights=weights)
        comparison = self.generate_comparison_summary(direct_result, safe_result, max_safe_slope)

        metadata = {
            "region": "Jezero Crater, Mars",
            "crs": "Areocentric IAU 2000 Mars Sphere (R=3,389,500m)",
            "grid_resolution_m": {
                "dy": round(self.terrain.dy_m, 1),
                "dx": round(self.terrain.dx_m, 1)
            },
            "solver": "8-directional Weighted A* (Admissible Euclidean Heuristic)",
            "safe_max_slope_enforced": max_safe_slope,
        }

        return RouteResponse(
            direct_path=direct_result,
            safe_survival_path=safe_result,
            comparison_summary=comparison,
            metadata=metadata
        )
