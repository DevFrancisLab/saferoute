"""
Example usage of the Haversine distance function and alert service for SafeRoute.

This demonstrates how to use the distance utilities to check if a driver
is near a hazard location and prevent alert fatigue.
"""

from core.utils import (
    haversine_distance, 
    is_driver_near_hazard, 
    get_distance_to_hazard,
    send_alert_with_fatigue_check,
    has_recent_alert
)
from core.models import Hazard


def example_distance_usage():
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


def example_alert_fatigue_prevention():
    """Example: Prevent alert fatigue by checking AlertLog."""
    
    print("\n" + "="*60)
    print("ALERT FATIGUE PREVENTION EXAMPLE")
    print("="*60 + "\n")
    
    # Create a test hazard if it doesn't exist
    hazard, created = Hazard.objects.get_or_create(
        type='BLACKSPOT',
        latitude=37.7749,
        longitude=-122.4194,
        defaults={
            'severity': 3,
        }
    )
    
    phone_number = "+1234567890"
    
    # First alert - should be sent
    print(f"Attempt 1: Sending alert to {phone_number}...")
    sent, message = send_alert_with_fatigue_check(phone_number, hazard, channel='SMS')
    print(f"  Result: {message}\n")
    
    # Second alert immediately - should be blocked
    print(f"Attempt 2: Sending another alert immediately...")
    sent, message = send_alert_with_fatigue_check(phone_number, hazard, channel='SMS')
    print(f"  Result: {message}\n")
    
    # Check recent alerts directly
    has_recent = has_recent_alert(phone_number, hazard.id, minutes=30)
    print(f"Has recent alert (30 min window): {has_recent}\n")
    
    # Try with different phone number - should be sent
    different_phone = "+9876543210"
    print(f"Attempt 3: Sending alert to different phone number...")
    sent, message = send_alert_with_fatigue_check(different_phone, hazard, channel='VOICE')
    print(f"  Result: {message}\n")
    
    # Try with different hazard - should be sent
    hazard2, _ = Hazard.objects.get_or_create(
        type='ACCIDENT',
        latitude=37.7800,
        longitude=-122.4150,
        defaults={
            'severity': 5,
        }
    )
    
    print(f"Attempt 4: Sending alert for different hazard...")
    sent, message = send_alert_with_fatigue_check(phone_number, hazard2, channel='SMS')
    print(f"  Result: {message}\n")


if __name__ == "__main__":
    example_distance_usage()
    # Uncomment to run alert example (requires Django setup):
    # example_alert_fatigue_prevention()

