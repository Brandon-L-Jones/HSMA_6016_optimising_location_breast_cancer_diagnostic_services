"""
travel.py
NHS-style distance and travel-time calculations.
"""

import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format="NHS TRAVEL | %(levelname)s | %(message)s")

def haversine_np(lat1, lon1, lat2, lon2):
    """
    Vectorized Haversine distance calculation.

    Args:
        lat1, lon1: GP lat/lon in degrees (arrays)
        lat2, lon2: Hospital lat/lon in degrees (arrays)

    Returns:
        Distance in miles (numpy.ndarray)
    """
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    R_miles = 3959.0
    return R_miles * c


def compute_distance_time(gp_coords: np.ndarray, hosp_coords: np.ndarray,
                               car_speed_mph: float, pt_speed_mph: float):
    """
    Compute distance and travel times from each GP to each hospital.

    Args:
        gp_coords: numpy.ndarray of shape (n_gps, 2) with latitude, longitude in degrees
        hosp_coords: numpy.ndarray of shape (n_hospitals, 2) with latitude, longitude in degrees
        car_speed_mph: average car speed (miles/hour)
        pt_speed_mph: average public transport speed (miles/hour)

    Returns:
        dist_miles: ndarray of shape (n_gps, n_hospitals)
        car_time_min: ndarray of shape (n_gps, n_hospitals)
        pt_time_min: ndarray of shape (n_gps, n_hospitals)
    """

    # --- Input validation ---
    if gp_coords.ndim != 2 or gp_coords.shape[1] != 2:
        logging.error("gp_coords must be (n_gps, 2)")
        raise ValueError("gp_coords must be (n_gps, 2) array")
    if hosp_coords.ndim != 2 or hosp_coords.shape[1] != 2:
        logging.error("hosp_coords must be (n_hospitals, 2)")
        raise ValueError("hosp_coords must be (n_hospitals, 2) array")
    if car_speed_mph <= 0 or pt_speed_mph <= 0:
        logging.error("Speeds must be positive")
        raise ValueError("Speeds must be positive")

    # Expand dims for broadcasting
    lat_g = gp_coords[:, 0][:, None]
    lon_g = gp_coords[:, 1][:, None]
    lat_h = hosp_coords[:, 0][None, :]
    lon_h = hosp_coords[:, 1][None, :]

    dist_miles = haversine_np(lat_g, lon_g, lat_h, lon_h)
    car_time_min = (dist_miles / car_speed_mph) * 60.0
    pt_time_min = (dist_miles / pt_speed_mph) * 60.0

    return dist_miles, car_time_min, pt_time_min
