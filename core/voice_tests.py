"""
Test script for Africa's Talking Voice API integration.

This demonstrates how to test the voice call functionality locally.
"""

import os
from core.utils import make_voice_call, send_voice_alert_with_fallback
from core.models import Hazard


def test_voice_call():
    """Test making a basic voice call."""
    print("="*60)
    print("TEST: Make Voice Call")
    print("="*60)
    
    test_phone = "+254712345678"
    
    print(f"Phone: {test_phone}")
    print("Message: LifeSaver Alert. Dangerous road section ahead. Reduce speed.\n")
    
    success, message = make_voice_call(test_phone)
    
    print(f"Status: {'✓ Initiated' if success else '✗ Failed'}")
    print(f"Response: {message}")
    print()


def test_voice_custom_message():
    """Test voice call with custom TTS message."""
    print("="*60)
    print("TEST: Voice Call with Custom Message")
    print("="*60)
    
    test_phone = "+254712345678"
    custom_msg = "Alert. Severe accident reported. Reduce speed immediately."
    
    print(f"Phone: {test_phone}")
    print(f"Message: {custom_msg}\n")
    
    success, message = make_voice_call(test_phone, custom_msg)
    
    print(f"Status: {'✓ Initiated' if success else '✗ Failed'}")
    print(f"Response: {message}")
    print()


def test_voice_with_sms_fallback():
    """Test voice call with SMS fallback."""
    print("="*60)
    print("TEST: Voice Call with SMS Fallback")
    print("="*60)
    
    hazard, _ = Hazard.objects.get_or_create(
        type='ACCIDENT',
        latitude=37.7800,
        longitude=-122.4150,
        defaults={'severity': 5}
    )
    
    test_phone = "+254712345678"
    
    print(f"Phone: {test_phone}")
    print(f"Hazard: {hazard.get_type_display()}")
    print("Strategy: Try voice call, fallback to SMS on failure\n")
    
    success, voice_msg, sms_msg = send_voice_alert_with_fallback(
        test_phone,
        hazard,
        voice_message="Critical hazard ahead. Reduce speed now.",
        sms_message="🚨 CRITICAL HAZARD AHEAD"
    )
    
    print(f"Voice Response: {voice_msg}")
    if sms_msg:
        print(f"SMS Fallback: {sms_msg}")
    print(f"\nStatus: {'✓ Success' if success else '✗ Failed'}")
    print()


def test_africastalking_voice_client():
    """Test if Africa's Talking voice client is available."""
    print("="*60)
    print("TEST: Africa's Talking Voice Client")
    print("="*60)
    
    username = os.getenv('AT_USERNAME')
    api_key = os.getenv('AT_API_KEY')
    
    if username and api_key:
        print(f"✓ Credentials found:")
        print(f"  AT_USERNAME: {username[:5]}...")
        print(f"  AT_API_KEY: {api_key[:5]}...")
        
        try:
            import africastalking
            print("✓ africastalking package available")
        except ImportError:
            print("✗ africastalking package not installed")
    else:
        print("✗ Missing credentials:")
        if not username:
            print("  - AT_USERNAME")
        if not api_key:
            print("  - AT_API_KEY")
    print()


def test_default_voice_message():
    """Display the default voice message."""
    print("="*60)
    print("TEST: Default Voice Message")
    print("="*60)
    
    default_msg = "LifeSaver Alert. Dangerous road section ahead. Reduce speed."
    print(f"Default Message: {default_msg}")
    print(f"Length: {len(default_msg)} characters")
    print(f"Estimated time: ~{len(default_msg) // 15} seconds\n")


def run_all_tests():
    """Run all voice call tests."""
    print("\n" + "="*60)
    print("SAFEROUTE VOICE CALL INTEGRATION TESTS")
    print("="*60 + "\n")
    
    test_africastalking_voice_client()
    test_default_voice_message()
    test_voice_call()
    test_voice_custom_message()
    test_voice_with_sms_fallback()
    
    print("="*60)
    print("TEST SUITE COMPLETE")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()
