"""
Example usage of the Haversine distance function for SafeRoute.

This demonstrates how to use the distance utilities to check if a driver
is near a hazard location.
"""

from core.utils import haversine_distance, is_driver_near_hazard, get_distance_to_hazard


def example_usage():
    """Example: Check if a driver is within 300 meters of a hazard."""
    
    # Example coordinates (San Francisco, CA area)
    driver_lat = 37.7749
    driver_lon = -122.4194
    
    # Hazard location nearby
    hazard_lat = 37.7755
    hazard_lon = -122.4188
    
    # Calculate raw distance
    distance = haversine_distance(driver_lat, driver_lon, hazard_lat, hazard_lon)
    print(f"Distance between driver and hazard: {distance:.2f} meters")
    
    # Check if driver is within 300 meters threshold
    within_threshold = is_driver_near_hazard(driver_lat, driver_lon, hazard_lat, hazard_lon, threshold_meters=300)
    print(f"Driver within 300 meters of hazard: {within_threshold}")
    
    # Get formatted distance
    distance_m, formatted = get_distance_to_hazard(driver_lat, driver_lon, hazard_lat, hazard_lon)
    print(f"Formatted distance: {formatted}")
    
    print("\n" + "="*60 + "\n")
    
    # Example 2: Driver far from hazard
    far_driver_lat = 37.8044
    far_driver_lon = -122.2712
    
    far_distance = haversine_distance(far_driver_lat, far_driver_lon, hazard_lat, hazard_lon)
    print(f"Distance (far driver): {far_distance:.2f} meters")
    
    within_far = is_driver_near_hazard(far_driver_lat, far_driver_lon, hazard_lat, hazard_lon)
    print(f"Far driver within 300 meters: {within_far}")
    
    distance_m, formatted = get_distance_to_hazard(far_driver_lat, far_driver_lon, hazard_lat, hazard_lon)
    print(f"Formatted distance: {formatted}")


if __name__ == "__main__":
    example_usage()
