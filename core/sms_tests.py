"""
Test script for Africa's Talking SMS integration.

This demonstrates how to test the SMS alert functionality locally.
"""

import os
from core.utils import send_sms_alert, send_sms_alert_with_fatigue_check, get_africastalking_client
from core.models import Hazard


def test_africastalking_credentials():
    """Test if Africa's Talking credentials are configured."""
    print("="*60)
    print("TEST: Africa's Talking Credentials")
    print("="*60)
    
    username = os.getenv('AT_USERNAME')
    api_key = os.getenv('AT_API_KEY')
    
    if username and api_key:
        print(f"✓ AT_USERNAME configured: {username[:5]}...")
        print(f"✓ AT_API_KEY configured: {api_key[:5]}...")
    else:
        print("✗ Missing credentials:")
        if not username:
            print("  - AT_USERNAME not set")
        if not api_key:
            print("  - AT_API_KEY not set")
    print()


def test_sms_client_initialization():
    """Test SMS client initialization."""
    print("="*60)
    print("TEST: SMS Client Initialization")
    print("="*60)
    
    client = get_africastalking_client()
    
    if client:
        print("✓ SMS client initialized successfully")
    else:
        print("✗ Failed to initialize SMS client")
        print("  Reason: Missing or invalid credentials")
    print()


def test_send_sms_alert():
    """Test sending a basic SMS alert."""
    print("="*60)
    print("TEST: Send SMS Alert")
    print("="*60)
    
    # Test with a sample phone number
    test_phone = "+254712345678"  # Example Kenyan number
    
    print(f"Sending SMS to: {test_phone}")
    success, message = send_sms_alert(test_phone)
    
    print(f"Result: {'✓ Success' if success else '✗ Failed'}")
    print(f"Message: {message}")
    print()


def test_send_sms_with_fatigue_check():
    """Test sending SMS with fatigue prevention."""
    print("="*60)
    print("TEST: Send SMS with Fatigue Check")
    print("="*60)
    
    test_phone = "+254712345678"
    
    # Create or get test hazard
    hazard, created = Hazard.objects.get_or_create(
        type='BLACKSPOT',
        latitude=37.7749,
        longitude=-122.4194,
        defaults={
            'severity': 3,
        }
    )
    
    print(f"Test hazard: {hazard.type} at ({hazard.latitude}, {hazard.longitude})")
    print(f"Phone number: {test_phone}\n")
    
    # First SMS - should succeed
    print("Attempt 1: Sending SMS...")
    success1, msg1 = send_sms_alert_with_fatigue_check(test_phone, hazard)
    print(f"Result: {'✓ Success' if success1 else '✗ Failed'}")
    print(f"Message: {msg1}\n")
    
    # Second SMS immediately - should be blocked
    print("Attempt 2: Sending SMS immediately after first...")
    success2, msg2 = send_sms_alert_with_fatigue_check(test_phone, hazard)
    print(f"Result: {'✓ Success' if success2 else '✗ Failed (Expected)'}")
    print(f"Message: {msg2}")
    print()


def test_custom_message():
    """Test sending SMS with custom message."""
    print("="*60)
    print("TEST: Send SMS with Custom Message")
    print("="*60)
    
    test_phone = "+254712345678"
    custom_msg = "🚨 ACCIDENT AHEAD: Major traffic congestion. Avoid route."
    
    print(f"Phone: {test_phone}")
    print(f"Message: {custom_msg}\n")
    
    success, message = send_sms_alert(test_phone, custom_message=custom_msg)
    
    print(f"Result: {'✓ Success' if success else '✗ Failed'}")
    print(f"Response: {message}")
    print()


def run_all_tests():
    """Run all SMS integration tests."""
    print("\n" + "="*60)
    print("SAFEROUTE SMS INTEGRATION TESTS")
    print("="*60 + "\n")
    
    test_africastalking_credentials()
    test_sms_client_initialization()
    test_send_sms_alert()
    test_send_sms_with_fatigue_check()
    test_custom_message()
    
    print("="*60)
    print("TEST SUITE COMPLETE")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()
