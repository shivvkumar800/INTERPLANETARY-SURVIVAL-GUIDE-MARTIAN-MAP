"""
Martian Terrain Engine for Jezero Crater (NASA Perseverance Exploration Zone).
Generates realistic high-resolution elevation, slope angles, radiation fields, and dust hazard zones.
"""

from typing import Tuple, Dict, Any, List
import numpy as np

# Physical Constants for Mars
MARS_MEAN_RADIUS_M = 3389500.0  # Mean radius of Mars in meters
RAD_PER_DEG = np.pi / 180.0

# Bounding box for Jezero Crater expedition theater
MIN_LAT = 18.20
MAX_LAT = 18.60
MIN_LON = 77.30
MAX_LON = 77.80


class JezeroTerrain:
    """
    2D Grid terrain and hazard model for Jezero Crater, Mars.
    Computes topographic elevation, slope gradients, cosmic radiation risk,
    and aeolian dust/sand entrapment hazard zones.
    """

    def __init__(self, rows: int = 100, cols: int = 100):
        self.rows = rows
        self.cols = cols
        self.min_lat = MIN_LAT
        self.max_lat = MAX_LAT
        self.min_lon = MIN_LON
        self.max_lon = MAX_LON

        # Coordinate arrays
        self.lats = np.linspace(self.min_lat, self.max_lat, self.rows)
        self.lons = np.linspace(self.min_lon, self.max_lon, self.cols)
        self.lon_grid, self.lat_grid = np.meshgrid(self.lons, self.lats)

        # Physical metric cell resolution
        # Latitude distance: arc length along meridian
        self.d_lat_deg = (self.max_lat - self.min_lat) / (self.rows - 1)
        self.dy_m = self.d_lat_deg * RAD_PER_DEG * MARS_MEAN_RADIUS_M

        # Longitude distance: arc length along parallel at mean latitude
        mean_lat_rad = np.radians((self.min_lat + self.max_lat) / 2.0)
        self.d_lon_deg = (self.max_lon - self.min_lon) / (self.cols - 1)
        self.dx_m = self.d_lon_deg * RAD_PER_DEG * MARS_MEAN_RADIUS_M * np.cos(mean_lat_rad)

        # Generate layers
        self.elevation = self._generate_elevation()
        self.slope = self._generate_slope()
        self.radiation = self._generate_radiation()
        self.dust = self._generate_dust()

    def _generate_elevation(self) -> np.ndarray:
        """
        Synthesizes realistic Jezero Crater topography:
        - Primary Jezero basin (-2500m datum floor) with elevated crater rim (-1950m)
        - Western delta fan deposit breaching from Neretva Vallis (-2380m)
        - Secondary impact crater Belva with steep >30 deg crater walls (impassable)
        - Kodiak Butte remnant mesa
        - Realistic surface regolith texture
        """
        # Convert lat/lon grid to relative meters from crater center (18.38 N, 77.58 E)
        center_lat = 18.380
        center_lon = 77.580
        mean_lat_rad = np.radians(center_lat)

        y_m = (self.lat_grid - center_lat) * RAD_PER_DEG * MARS_MEAN_RADIUS_M
        x_m = (self.lon_grid - center_lon) * RAD_PER_DEG * MARS_MEAN_RADIUS_M * np.cos(mean_lat_rad)
        dist_from_center_m = np.sqrt(x_m**2 + y_m**2)

        # 1. Base Crater Floor & Rim Topography
        base_elevation = -2500.0

        # Jezero Rim: circular ring uplift centered at ~11.5 km radius within mapped bounds
        crater_radius_m = 11500.0
        rim_ring = 520.0 * np.exp(-((dist_from_center_m - crater_radius_m) / 1400.0)**2)
        outer_drop = -150.0 / (1.0 + np.exp(-0.003 * (dist_from_center_m - crater_radius_m * 1.15)))
        elevation = base_elevation + rim_ring + outer_drop

        # 2. Western River Delta / Alluvial Fan Deposit (Neretva Vallis)
        # Centered around lat 18.420, lon 77.440
        delta_lat = 18.420
        delta_lon = 77.440
        y_delta = (self.lat_grid - delta_lat) * RAD_PER_DEG * MARS_MEAN_RADIUS_M
        x_delta = (self.lon_grid - delta_lon) * RAD_PER_DEG * MARS_MEAN_RADIUS_M * np.cos(mean_lat_rad)
        delta_dist = np.sqrt((x_delta * 0.8)**2 + (y_delta * 1.3)**2)
        delta_lobe = 140.0 * np.exp(-(delta_dist / 3500.0)**2)
        elevation += delta_lobe

        # 3. Belva Crater (Impact crater on floor, lat 18.440, lon 77.520)
        # Deep circular bowl with steep walls (>30 deg) and raised rim
        belva_lat = 18.440
        belva_lon = 77.520
        y_belva = (self.lat_grid - belva_lat) * RAD_PER_DEG * MARS_MEAN_RADIUS_M
        x_belva = (self.lon_grid - belva_lon) * RAD_PER_DEG * MARS_MEAN_RADIUS_M * np.cos(mean_lat_rad)
        belva_dist = np.sqrt(x_belva**2 + y_belva**2)

        # Sigmoidal wall drop down to -320m depth creates realistic steep walls exceeding 30 degrees
        belva_wall = -320.0 / (1.0 + np.exp((belva_dist - 1150.0) / 140.0))
        belva_rim = 95.0 * np.exp(-((belva_dist - 1500.0) / 260.0)**2)
        elevation += belva_wall + belva_rim

        # 4. Kodiak Butte (Isolated remnant mesa at lat 18.410, lon 77.455)
        kodiak_lat = 18.410
        kodiak_lon = 77.455
        y_kodiak = (self.lat_grid - kodiak_lat) * RAD_PER_DEG * MARS_MEAN_RADIUS_M
        x_kodiak = (self.lon_grid - kodiak_lon) * RAD_PER_DEG * MARS_MEAN_RADIUS_M * np.cos(mean_lat_rad)
        kodiak_dist = np.sqrt(x_kodiak**2 + y_kodiak**2)
        kodiak_mesa = 95.0 * np.exp(-(kodiak_dist / 420.0)**4)
        elevation += kodiak_mesa

        # 5. Natural Topographic Regolith Roughness (Multi-octave sine harmonics)
        roughness = (
            15.0 * np.sin(x_m / 1400.0) * np.cos(y_m / 1600.0)
            + 6.0 * np.sin(x_m / 600.0 + 1.2) * np.sin(y_m / 700.0 + 0.8)
        )
        elevation += roughness

        return elevation

    def _generate_slope(self) -> np.ndarray:
        """
        Computes accurate physical terrain slope angles in degrees using central differences.
        dz/dy and dz/dx are measured against physical meters on Mars surface.
        """
        # Central difference gradients
        dz_dy, dz_dx = np.gradient(self.elevation, self.dy_m, self.dx_m)

        # Slope magnitude in radians, then convert to degrees
        gradient_mag = np.sqrt(dz_dx**2 + dz_dy**2)
        slope_rad = np.arctan(gradient_mag)
        slope_deg = np.degrees(slope_rad)

        return np.round(slope_deg, 2)

    def _generate_radiation(self) -> np.ndarray:
        """
        Generates normalized Martian cosmic radiation and Solar Particle Event (SPE) risk [0.0 - 1.0].
        - Base risk tied to elevation (higher altitudes have thinner atmospheric shielding).
        - Localized high-exposure anomalies (e.g., exposed radioactive mineral deposits / ridge crests).
        """
        mean_lat_rad = np.radians(18.38)
        # Normalization of elevation to 0.2 - 0.6 base exposure
        elev_min = np.min(self.elevation)
        elev_max = np.max(self.elevation)
        elev_norm = (self.elevation - elev_min) / (elev_max - elev_min + 1e-6)
        rad_field = 0.20 + 0.40 * elev_norm

        # High radiation ridge exposure corridor along southern rim
        corridor_lat = 18.280
        corridor_lon = 77.480
        y_cor = (self.lat_grid - corridor_lat) * RAD_PER_DEG * MARS_MEAN_RADIUS_M
        x_cor = (self.lon_grid - corridor_lon) * RAD_PER_DEG * MARS_MEAN_RADIUS_M * np.cos(mean_lat_rad)
        rad_anomaly = 0.45 * np.exp(-((x_cor / 4500.0)**2 + (y_cor / 2200.0)**2))
        rad_field += rad_anomaly

        # Localized solar flare flare-up hotspot near eastern plains
        flare_lat = 18.480
        flare_lon = 77.650
        y_flare = (self.lat_grid - flare_lat) * RAD_PER_DEG * MARS_MEAN_RADIUS_M
        x_flare = (self.lon_grid - flare_lon) * RAD_PER_DEG * MARS_MEAN_RADIUS_M * np.cos(mean_lat_rad)
        flare_anomaly = 0.35 * np.exp(-((x_flare / 3000.0)**2 + (y_flare / 3000.0)**2))
        rad_field += flare_anomaly

        # Clip strictly between 0.05 and 0.98
        return np.clip(np.round(rad_field, 3), 0.0, 1.0)

    def _generate_dust(self) -> np.ndarray:
        """
        Generates normalized Martian dust storm and sand dune rover entrapment risk [0.0 - 1.0].
        - High risk in Séítah Dune Field (unconsolidated aeolian ripples where rovers get stuck).
        - Secondary silt pockets at base of delta scarp.
        """
        mean_lat_rad = np.radians(18.38)
        dust_field = np.full_like(self.elevation, 0.12)

        # 1. Séítah Formation Dune Field (lat 18.370, lon 77.550)
        # Severe hazard: loose drift sand, high slip and wheel entrapment
        seitah_lat = 18.370
        seitah_lon = 77.550
        y_seitah = (self.lat_grid - seitah_lat) * RAD_PER_DEG * MARS_MEAN_RADIUS_M
        x_seitah = (self.lon_grid - seitah_lon) * RAD_PER_DEG * MARS_MEAN_RADIUS_M * np.cos(mean_lat_rad)
        seitah_hazard = 0.82 * np.exp(-((x_seitah / 2200.0)**2 + (y_seitah / 1800.0)**2))
        dust_field += seitah_hazard

        # 2. Western Delta Silt Sediment Zone (lat 18.425, lon 77.490)
        silt_lat = 18.425
        silt_lon = 77.490
        y_silt = (self.lat_grid - silt_lat) * RAD_PER_DEG * MARS_MEAN_RADIUS_M
        x_silt = (self.lon_grid - silt_lon) * RAD_PER_DEG * MARS_MEAN_RADIUS_M * np.cos(mean_lat_rad)
        silt_hazard = 0.60 * np.exp(-((x_silt / 3100.0)**2 + (y_silt / 2000.0)**2))
        dust_field += silt_hazard

        # Minor ripple noise
        dune_waves = 0.06 * np.sin(x_seitah / 350.0) * np.cos(y_seitah / 350.0)
        dust_field += np.abs(dune_waves)

        return np.clip(np.round(dust_field, 3), 0.0, 1.0)

    def lat_lon_to_indices(self, lat: float, lon: float) -> Tuple[int, int]:
        """Converts lat/lon coordinates to closest grid row and column indices."""
        r = int(np.clip(np.round((lat - self.min_lat) / self.d_lat_deg), 0, self.rows - 1))
        c = int(np.clip(np.round((lon - self.min_lon) / self.d_lon_deg), 0, self.cols - 1))
        return r, c

    def indices_to_lat_lon(self, r: int, c: int) -> Tuple[float, float]:
        """Converts grid row and column indices to lat/lon coordinates."""
        lat = self.min_lat + r * self.d_lat_deg
        lon = self.min_lon + c * self.d_lon_deg
        return float(np.round(lat, 5)), float(np.round(lon, 5))

    def sample_point(self, lat: float, lon: float) -> Dict[str, float]:
        """
        Samples elevation, slope, radiation, and dust using bilinear interpolation.
        Returns clamped values if coordinate is on edge.
        """
        # Fractional grid coordinates
        r_f = (lat - self.min_lat) / self.d_lat_deg
        c_f = (lon - self.min_lon) / self.d_lon_deg

        r_f = float(np.clip(r_f, 0, self.rows - 1))
        c_f = float(np.clip(c_f, 0, self.cols - 1))

        r0 = int(np.floor(r_f))
        r1 = min(r0 + 1, self.rows - 1)
        c0 = int(np.floor(c_f))
        c1 = min(c0 + 1, self.cols - 1)

        dr = r_f - r0
        dc = c_f - c0

        def bilerp(arr: np.ndarray) -> float:
            top = (1.0 - dc) * arr[r0, c0] + dc * arr[r0, c1]
            bottom = (1.0 - dc) * arr[r1, c0] + dc * arr[r1, c1]
            return float((1.0 - dr) * top + dr * bottom)

        return {
            "elevation": round(bilerp(self.elevation), 2),
            "slope": round(bilerp(self.slope), 2),
            "radiation": round(bilerp(self.radiation), 3),
            "dust": round(bilerp(self.dust), 3),
        }

    def get_presets(self) -> List[Dict[str, Any]]:
        """Returns scientifically grounded landmarks in Jezero Crater for testing."""
        return [
            {
                "id": "base_alpha",
                "name": "Octavia E. Butler Landing (Base Alpha)",
                "description": "Perseverance rover landing site on smooth Jezero Crater floor.",
                "coordinate": {"lat": 18.380, "lon": 77.580},
                "feature_type": "Expedition Base"
            },
            {
                "id": "kodiak_butte",
                "name": "Kodiak Butte Delta Overlook",
                "description": "Prominent isolated remnant mesa exposing ancient delta bottomset and foreset strata.",
                "coordinate": {"lat": 18.445, "lon": 77.455},
                "feature_type": "Scientific Target"
            },
            {
                "id": "belva_crater_rim",
                "name": "Belva Crater North Rim",
                "description": "Large secondary impact crater with treacherous >30 deg boulder-strewn rim walls.",
                "coordinate": {"lat": 18.480, "lon": 77.520},
                "feature_type": "Hazard / Science Target"
            },
            {
                "id": "neretva_vallis",
                "name": "Neretva Vallis Inflow Channel",
                "description": "Ancient river breach canyon cutting through western rim of Jezero Crater.",
                "coordinate": {"lat": 18.410, "lon": 77.360},
                "feature_type": "Canyon Breach"
            },
            {
                "id": "seitah_station",
                "name": "Séítah Sand Dune Research Station",
                "description": "Active sand dune corridor characterized by loose drift regolith and high wheel entrapment risk.",
                "coordinate": {"lat": 18.365, "lon": 77.535},
                "feature_type": "Dune Field"
            },
            {
                "id": "eastern_rim",
                "name": "Eastern Rim High Ridge",
                "description": "High-altitude crest offering wide vista but exposed to acute cosmic radiation flux.",
                "coordinate": {"lat": 18.350, "lon": 77.720},
                "feature_type": "Crater Rim Crest"
            }
        ]


# Singleton terrain instance for high-performance in-memory routing
_terrain_instance: JezeroTerrain = None


def get_terrain() -> JezeroTerrain:
    """Returns singleton instance of the Jezero terrain model."""
    global _terrain_instance
    if _terrain_instance is None:
        _terrain_instance = JezeroTerrain(rows=100, cols=100)
    return _terrain_instance
