import math
import os
from typing import Tuple
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q


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


# Alert Service Functions


def has_recent_alert(phone_number: str, hazard_id: int, minutes: int = 30) -> bool:
    """
    Check if an alert was recently sent to this phone number for this hazard.
    
    Prevents alert fatigue by not sending duplicate alerts within the specified timeframe.
    
    Args:
        phone_number: The phone number to check
        hazard_id: The hazard ID to check
        minutes: Time window to check (default: 30 minutes)
    
    Returns:
        True if a recent alert exists, False otherwise
    """
    from .models import AlertLog
    
    time_threshold = timezone.now() - timedelta(minutes=minutes)
    
    recent_alert = AlertLog.objects.filter(
        phone_number=phone_number,
        hazard_id=hazard_id,
        sent_at__gte=time_threshold
    ).exists()
    
    return recent_alert


def send_alert_with_fatigue_check(
    phone_number: str, 
    hazard, 
    channel: str = 'SMS',
    alert_cooldown_minutes: int = 30
) -> Tuple[bool, str]:
    """
    Send an alert to a driver, with alert fatigue prevention.
    
    Checks if an alert was recently sent to the same phone number for the same hazard.
    If not, creates a new AlertLog entry and returns True.
    
    Args:
        phone_number: The driver's phone number
        hazard: The Hazard instance to alert about
        channel: Alert channel ('SMS' or 'VOICE')
        alert_cooldown_minutes: Minutes to wait before sending another alert (default: 30)
    
    Returns:
        Tuple of (alert_sent: bool, message: str)
        - alert_sent: True if alert was sent, False if skipped due to recent alert
        - message: Descriptive message about what happened
    """
    from .models import AlertLog
    
    # Check if a recent alert exists
    if has_recent_alert(phone_number, hazard.id, alert_cooldown_minutes):
        return False, f"Alert for hazard {hazard.id} already sent to {phone_number} within last {alert_cooldown_minutes} minutes"
    
    # Create new alert log entry
    try:
        alert_log = AlertLog.objects.create(
            phone_number=phone_number,
            hazard=hazard,
            channel=channel
        )
        return True, f"Alert sent to {phone_number} via {channel} for hazard {hazard.id}"
    except Exception as e:
        return False, f"Error sending alert: {str(e)}"


# SMS Integration (Africa's Talking)


def get_africastalking_client():
    """
    Initialize Africa's Talking SMS client with credentials from environment variables.
    
    Environment Variables Required:
        AT_USERNAME: Your Africa's Talking username
        AT_API_KEY: Your Africa's Talking API key
    
    Returns:
        SMS client instance or None if credentials are missing
    """
    try:
        import africastalking
    except ImportError:
        return None
    
    username = os.getenv('AT_USERNAME')
    api_key = os.getenv('AT_API_KEY')
    
    if not username or not api_key:
        return None
    
    # Initialize Africa's Talking
    africastalking.initialize(username, api_key)
    sms = africastalking.SMS
    
    return sms


def send_sms_alert(phone_number: str, custom_message: str = None) -> Tuple[bool, str]:
    """
    Send SMS alert via Africa's Talking API.
    
    Args:
        phone_number: Recipient phone number (include country code, e.g., +254712345678)
        custom_message: Optional custom message. If None, uses default SafeRoute alert message.
    
    Returns:
        Tuple of (success: bool, response_message: str)
    """
    # Default SafeRoute alert message
    DEFAULT_ALERT = "⚠️ LifeSaver Alert: Dangerous road section ahead. Please slow down."
    
    message = custom_message or DEFAULT_ALERT
    
    # Get SMS client
    sms_client = get_africastalking_client()
    
    if not sms_client:
        return False, "Africa's Talking credentials not configured. Set AT_USERNAME and AT_API_KEY environment variables."
    
    try:
        # Send SMS
        response = sms_client.send(message, [phone_number])
        
        # Check response
        if response['SMSMessageData']['Recipients']:
            recipient = response['SMSMessageData']['Recipients'][0]
            
            if recipient['status'] == 'Success':
                return True, f"SMS sent successfully to {phone_number}"
            else:
                error_msg = recipient.get('status', 'Unknown error')
                return False, f"SMS delivery failed: {error_msg}"
        else:
            return False, "No recipients in response"
            
    except Exception as e:
        return False, f"Error sending SMS: {str(e)}"


def send_sms_alert_with_fatigue_check(
    phone_number: str,
    hazard,
    custom_message: str = None
) -> Tuple[bool, str]:
    """
    Send SMS alert with alert fatigue prevention.
    
    Combines fatigue check and SMS sending in one operation.
    
    Args:
        phone_number: Recipient phone number
        hazard: The Hazard instance
        custom_message: Optional custom message
    
    Returns:
        Tuple of (success: bool, response_message: str)
    """
    # First check fatigue
    alert_allowed, fatigue_message = send_alert_with_fatigue_check(
        phone_number, 
        hazard, 
        channel='SMS',
        alert_cooldown_minutes=30
    )
    
    if not alert_allowed:
        return False, fatigue_message
    
    # If allowed, send the SMS
    success, sms_message = send_sms_alert(phone_number, custom_message)
    
    return success, sms_message
