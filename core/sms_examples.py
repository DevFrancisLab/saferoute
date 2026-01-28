"""
Practical examples of SMS integration in SafeRoute.

These examples show real-world usage patterns.
"""

from core.models import Hazard
from core.utils import (
    send_sms_alert,
    send_sms_alert_with_fatigue_check,
    is_driver_near_hazard,
    haversine_distance
)


def example_1_basic_alert():
    """
    Example 1: Send a basic SMS alert to a driver.
    """
    print("EXAMPLE 1: Send Basic SMS Alert")
    print("-" * 60)
    
    driver_phone = "+254712345678"
    
    success, message = send_sms_alert(driver_phone)
    
    print(f"Recipient: {driver_phone}")
    print(f"Status: {'✓ Sent' if success else '✗ Failed'}")
    print(f"Response: {message}")
    print()


def example_2_custom_message():
    """
    Example 2: Send SMS with custom message.
    """
    print("EXAMPLE 2: Send Custom Message Alert")
    print("-" * 60)
    
    driver_phone = "+254712345678"
    hazard_type = "ACCIDENT"
    severity = 5
    
    custom_msg = f"🚨 SEVERE {hazard_type} ahead! Avoid this area immediately."
    
    success, message = send_sms_alert(driver_phone, custom_message=custom_msg)
    
    print(f"Recipient: {driver_phone}")
    print(f"Message: {custom_msg}")
    print(f"Status: {'✓ Sent' if success else '✗ Failed'}")
    print(f"Response: {message}")
    print()


def example_3_alert_nearby_driver():
    """
    Example 3: Alert a driver if they're near a hazard.
    """
    print("EXAMPLE 3: Alert Driver Near Hazard")
    print("-" * 60)
    
    # Driver coordinates
    driver_lat = 37.7749
    driver_lon = -122.4194
    
    # Get all hazards
    hazards = Hazard.objects.all()
    
    for hazard in hazards:
        # Check if driver is within 500m
        if is_driver_near_hazard(driver_lat, driver_lon, hazard.latitude, hazard.longitude, threshold_meters=500):
            print(f"🚗 Driver near {hazard.get_type_display()}")
            print(f"   Distance: {haversine_distance(driver_lat, driver_lon, hazard.latitude, hazard.longitude):.0f}m")
            
            # Send alert with fatigue check
            success, msg = send_sms_alert_with_fatigue_check("+254712345678", hazard)
            print(f"   Alert: {'✓ Sent' if success else '✗ Blocked/Failed'}")
            print()


def example_4_batch_alerts():
    """
    Example 4: Send alerts to multiple drivers near a hazard.
    """
    print("EXAMPLE 4: Batch Alert to Multiple Drivers")
    print("-" * 60)
    
    # Get a hazard
    hazard = Hazard.objects.filter(type='ACCIDENT').first()
    
    if not hazard:
        print("No accident hazard found")
        return
    
    # List of drivers to alert
    drivers = [
        ("+254712345678", 37.7745, -122.4195),
        ("+254798765432", 37.7750, -122.4190),
        ("+254722111111", 37.7755, -122.4185),
    ]
    
    print(f"Alerting drivers near {hazard.get_type_display()}")
    print(f"Hazard location: ({hazard.latitude}, {hazard.longitude})\n")
    
    alerted = 0
    for phone, lat, lon in drivers:
        # Check if driver is near
        if is_driver_near_hazard(lat, lon, hazard.latitude, hazard.longitude, threshold_meters=300):
            success, msg = send_sms_alert_with_fatigue_check(phone, hazard)
            if success:
                alerted += 1
                print(f"✓ {phone}: Alert sent")
            else:
                print(f"✗ {phone}: {msg}")
    
    print(f"\nTotal alerts sent: {alerted}/{len(drivers)}")
    print()


def example_5_severity_based_message():
    """
    Example 5: Send different messages based on hazard severity.
    """
    print("EXAMPLE 5: Severity-Based Alert Messages")
    print("-" * 60)
    
    hazard = Hazard.objects.first()
    
    if not hazard:
        print("No hazards found")
        return
    
    # Build severity-based message
    severity_messages = {
        1: "⚠️ CAUTION: Minor issue ahead. Drive carefully.",
        2: "⚠️ WARNING: Moderate hazard ahead. Slow down.",
        3: "⚠️ ALERT: Dangerous condition ahead. Reduce speed.",
        4: "🚨 DANGER: Severe hazard ahead. Avoid if possible.",
        5: "🚨 CRITICAL: Extreme danger ahead. Avoid area completely."
    }
    
    message = severity_messages.get(hazard.severity, "⚠️ Alert: Hazard ahead.")
    
    print(f"Hazard: {hazard.get_type_display()}")
    print(f"Severity: {hazard.severity}/5")
    print(f"Message: {message}\n")
    
    success, response = send_sms_alert("+254712345678", custom_message=message)
    print(f"Status: {'✓ Sent' if success else '✗ Failed'}")
    print(f"Response: {response}")
    print()


def example_6_no_fatigue_spam():
    """
    Example 6: Demonstrate fatigue prevention.
    """
    print("EXAMPLE 6: Alert Fatigue Prevention")
    print("-" * 60)
    
    hazard = Hazard.objects.first()
    if not hazard:
        print("No hazards found")
        return
    
    driver_phone = "+254712345678"
    
    print(f"Attempting to send multiple alerts to: {driver_phone}")
    print(f"For hazard: {hazard.get_type_display()}\n")
    
    # First alert - should succeed
    print("Attempt 1: First alert...")
    success1, msg1 = send_sms_alert_with_fatigue_check(driver_phone, hazard)
    print(f"  Result: {msg1}\n")
    
    # Second alert - should be blocked
    print("Attempt 2: Immediate second alert...")
    success2, msg2 = send_sms_alert_with_fatigue_check(driver_phone, hazard)
    print(f"  Result: {msg2}\n")
    
    # Third alert - should be blocked
    print("Attempt 3: Third alert...")
    success3, msg3 = send_sms_alert_with_fatigue_check(driver_phone, hazard)
    print(f"  Result: {msg3}\n")
    
    print("Alert fatigue prevention working: ✓" if not success2 and not success3 else "✗")
    print()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("SAFEROUTE SMS PRACTICAL EXAMPLES")
    print("="*60 + "\n")
    
    # Note: These require Django setup and should be run in shell
    # python manage.py shell < core/sms_examples.py
    
    print("Run these examples in Django shell:")
    print("  python manage.py shell")
    print("  >>> exec(open('core/sms_examples.py').read())")
    print()
    print("Or run individual examples:")
    print("  >>> from core.sms_examples import example_1_basic_alert")
    print("  >>> example_1_basic_alert()")
