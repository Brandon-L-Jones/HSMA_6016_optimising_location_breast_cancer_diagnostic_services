"""
demand.py
NHS-style demand and access metrics computation.
"""

import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format="NHS DEMAND | %(levelname)s | %(message)s")

def nearest_metrics(
    dist_miles: np.ndarray,
    car_time_min: np.ndarray,
    pt_time_min: np.ndarray,
    monthly_referrals: np.ndarray,
    car_speed_mph: float,
    fuel_cost_per_mile: float,
    co2_per_mile: float
):
    """
    Compute nearest-hospital metrics per GP practice.

    Args:
        dist_miles (ndarray): distance to hospitals (GPs x Hospitals)
        car_time_min (ndarray): travel time by car (GPs x Hospitals)
        pt_time_min (ndarray): travel time by public transport (GPs x Hospitals)
        monthly_referrals (ndarray): number of monthly referrals per GP
        car_speed_mph (float): assumed car speed
        fuel_cost_per_mile (float): fuel cost
        co2_per_mile (float): CO2 emissions per mile

    Returns:
        tuple of ndarrays:
            nearest_dist: nearest hospital distance (miles)
            nearest_car_time: nearest hospital travel time by car (minutes)
            nearest_pt_time: nearest hospital travel time by public transport (minutes)
            fuel_cost: fuel cost to nearest hospital
            co2: CO2 emissions to nearest hospital
            weighted_car: referrals * nearest car travel time
            weighted_pt: referrals * nearest PT travel time
            weighted_access_score: weighted access metric (NHS-friendly)
    """

    # --- Input validation ---
    if not all(isinstance(arr, np.ndarray) for arr in [dist_miles, car_time_min, pt_time_min, monthly_referrals]):
        logging.error("All input arrays must be numpy.ndarray")
        raise TypeError("Inputs must be numpy arrays")

    nearest_dist = np.min(dist_miles, axis=1)
    nearest_car_time = np.min(car_time_min, axis=1)
    nearest_pt_time = np.min(pt_time_min, axis=1)

    # Fuel cost & CO2
    miles = nearest_car_time / 60.0 * car_speed_mph
    fuel_cost = miles * fuel_cost_per_mile
    co2 = miles * co2_per_mile

    # Weighted metrics
    weighted_car = monthly_referrals * nearest_car_time
    weighted_pt = monthly_referrals * nearest_pt_time

    # NHS-friendly composite access score: lower is better
    weighted_access_score = weighted_car + weighted_pt

    return (
        nearest_dist,
        nearest_car_time,
        nearest_pt_time,
        fuel_cost,
        co2,
        weighted_car,
        weighted_pt,
        weighted_access_score
    )
