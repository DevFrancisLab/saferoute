import math
from typing import Tuple


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees).
    
    Args:
        lat1: Latitude of point 1 in decimal degrees
        lon1: Longitude of point 1 in decimal degrees
        lat2: Latitude of point 2 in decimal degrees
        lon2: Longitude of point 2 in decimal degrees
    
    Returns:
        Distance in meters
    """
    # Earth's radius in meters
    EARTH_RADIUS_METERS = 6371000
    
    # Convert decimal degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    # Distance in meters
    distance = EARTH_RADIUS_METERS * c
    
    return distance


def is_driver_near_hazard(
    driver_lat: float, 
    driver_lon: float, 
    hazard_lat: float, 
    hazard_lon: float, 
    threshold_meters: float = 300
) -> bool:
    """
    Check if a driver is within a specified distance of a hazard.
    
    Args:
        driver_lat: Driver's latitude
        driver_lon: Driver's longitude
        hazard_lat: Hazard's latitude
        hazard_lon: Hazard's longitude
        threshold_meters: Distance threshold in meters (default: 300)
    
    Returns:
        True if driver is within threshold distance, False otherwise
    """
    distance = haversine_distance(driver_lat, driver_lon, hazard_lat, hazard_lon)
    return distance <= threshold_meters


def get_distance_to_hazard(
    driver_lat: float, 
    driver_lon: float, 
    hazard_lat: float, 
    hazard_lon: float
) -> Tuple[float, str]:
    """
    Get the distance between a driver and a hazard, with formatted output.
    
    Args:
        driver_lat: Driver's latitude
        driver_lon: Driver's longitude
        hazard_lat: Hazard's latitude
        hazard_lon: Hazard's longitude
    
    Returns:
        Tuple of (distance_in_meters, formatted_string)
    """
    distance = haversine_distance(driver_lat, driver_lon, hazard_lat, hazard_lon)
    
    if distance < 1000:
        formatted = f"{distance:.1f} meters"
    else:
        formatted = f"{distance / 1000:.2f} km"
    
    return distance, formatted
