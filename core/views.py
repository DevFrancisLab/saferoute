"""
Africa's Talking USSD Integration

Handles USSD requests from Africa's Talking API for SafeRoute
"""

from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import logging
from core.models import Report

logger = logging.getLogger(__name__)

# USSD Session storage (in production, use Redis or Django sessions)
# Format: {phone_number: {'state': 'menu_state', 'data': {}}}
ussd_sessions = {}

# USSD Menu States
STATE_MENU = "menu"
STATE_HAZARD_TYPE = "hazard_type"
STATE_CONFIRM = "confirm"


def get_session(phone_number):
    """Get or create USSD session for phone number."""
    if phone_number not in ussd_sessions:
        ussd_sessions[phone_number] = {
            'state': STATE_MENU,
            'data': {}
        }
    return ussd_sessions[phone_number]


def clear_session(phone_number):
    """Clear USSD session for phone number."""
    if phone_number in ussd_sessions:
        del ussd_sessions[phone_number]


def build_main_menu():
    """Build main USSD menu."""
    menu = (
        "CON Welcome to SafeRoute\n"
        "Report hazards on the road\n"
        "\n"
        "1. Report Hazard\n"
        "2. Get Alerts\n"
        "3. Exit"
    )
    return menu


def build_hazard_menu():
    """Build hazard type selection menu."""
    menu = (
        "CON Select hazard type:\n"
        "\n"
        "1. Accident\n"
        "2. Bad Road\n"
        "3. Pedestrians\n"
        "4. Black Spot\n"
        "0. Back"
    )
    return menu


def get_hazard_type(code):
    """Get hazard type from user selection."""
    hazard_map = {
        '1': 'ACCIDENT',
        '2': 'BAD_ROAD',
        '3': 'PEDESTRIANS',
        '4': 'BLACKSPOT',
    }
    return hazard_map.get(code)


def get_approximate_location():
    """
    Get approximate location for report.
    
    In production, this would:
    - Get location from GPS if available
    - Use cell tower triangulation
    - Use last known location
    
    For hackathon MVP, using a default location (Nairobi area)
    """
    return {
        'latitude': -1.2921,  # Nairobi, Kenya
        'longitude': 36.8219
    }


@csrf_exempt
@require_http_methods(["POST"])
def ussd_webhook(request):
    """
    Africa's Talking USSD Webhook Handler
    
    POST Request format from Africa's Talking:
    {
        "sessionId": "12345",
        "phoneNumber": "+254712345678",
        "text": "1*2",
        "serviceCode": "123456"
    }
    
    Response format:
    - "CON message" = Continue session
    - "END message" = End session
    """
    try:
        # Parse request data
        session_id = request.POST.get('sessionId', '')
        phone_number = request.POST.get('phoneNumber', '')
        user_input = request.POST.get('text', '')
        service_code = request.POST.get('serviceCode', '')
        
        logger.info(f"USSD Request: Phone={phone_number}, Input={user_input}")
        
        # Validate phone number
        if not phone_number:
            return HttpResponse("END Error: Phone number required")
        
        # Get session
        session = get_session(phone_number)
        
        # Route based on current state
        if session['state'] == STATE_MENU:
            response = handle_main_menu(phone_number, user_input, session)
        elif session['state'] == STATE_HAZARD_TYPE:
            response = handle_hazard_selection(phone_number, user_input, session)
        elif session['state'] == STATE_CONFIRM:
            response = handle_confirmation(phone_number, user_input, session)
        else:
            response = "END Error: Invalid session state"
        
        logger.info(f"USSD Response: {response[:50]}...")
        return HttpResponse(response)
        
    except Exception as e:
        logger.error(f"USSD Error: {str(e)}", exc_info=True)
        return HttpResponse("END Error: Please try again later")


def handle_main_menu(phone_number, user_input, session):
    """Handle main menu selections."""
    
    if user_input == '':
        # Initial request - show main menu
        return build_main_menu()
    
    if user_input == '1':
        # User selected "Report Hazard"
        session['state'] = STATE_HAZARD_TYPE
        session['data']['phone_number'] = phone_number
        return build_hazard_menu()
    
    elif user_input == '2':
        # Get Alerts - not implemented for MVP
        response = (
            "CON SafeRoute Alerts\n"
            "\n"
            "Alerts feature coming soon.\n"
            "Please report hazards to help drivers.\n"
            "\n"
            "1. Back to Menu\n"
            "2. Exit"
        )
        return response
    
    elif user_input == '3':
        # Exit
        clear_session(phone_number)
        return "END Thank you for using SafeRoute!"
    
    else:
        # Invalid input
        return build_main_menu()


def handle_hazard_selection(phone_number, user_input, session):
    """Handle hazard type selection."""
    
    # Extract the last digit from input (e.g., '1*1' -> '1', '1' -> '1')
    parts = user_input.split('*')
    last_input = parts[-1] if parts else ''
    
    hazard_type = get_hazard_type(last_input)
    
    if last_input == '0':
        # Go back to main menu
        session['state'] = STATE_MENU
        session['data'].clear()
        return build_main_menu()
    
    elif hazard_type:
        # Valid hazard type selected
        session['data']['hazard_type'] = hazard_type
        
        # Get approximate location
        location = get_approximate_location()
        session['data']['latitude'] = location['latitude']
        session['data']['longitude'] = location['longitude']
        
        # Show confirmation
        hazard_display = hazard_type.replace('_', ' ').title()
        response = (
            f"CON Confirm Report\n"
            f"\n"
            f"Hazard: {hazard_display}\n"
            f"Location: Nairobi area\n"
            f"\n"
            f"1. Confirm & Submit\n"
            f"0. Cancel"
        )
        session['state'] = STATE_CONFIRM
        return response
    
    else:
        # Invalid input
        return build_hazard_menu()


def handle_confirmation(phone_number, user_input, session):
    """Handle report confirmation and submission."""
    
    # Extract the last digit from input (e.g., '1*1*1' -> '1', '1' -> '1')
    parts = user_input.split('*')
    last_input = parts[-1] if parts else ''
    
    if last_input == '1':
        # User confirmed - save report
        try:
            report = Report.objects.create(
                phone_number=phone_number,
                hazard_type=session['data'].get('hazard_type'),
                latitude=session['data'].get('latitude'),
                longitude=session['data'].get('longitude')
            )
            
            hazard_type = report.get_hazard_type_display()
            logger.info(f"Report created: ID={report.id}, Phone={phone_number}, Type={hazard_type}")
            
            # Clear session
            clear_session(phone_number)
            
            # Return success message
            return (
                "END Thank you!\n"
                f"Your {hazard_type} report\n"
                "has been received.\n"
                "\n"
                "Nearby drivers will\n"
                "be alerted."
            )
            
        except Exception as e:
            logger.error(f"Failed to save report: {str(e)}", exc_info=True)
            clear_session(phone_number)
            return "END Error saving report. Please try again."
    
    elif last_input == '0':
        # User cancelled
        session['state'] = STATE_MENU
        session['data'].clear()
        response = (
            "CON Report Cancelled\n"
            "\n"
            "1. Report Another Hazard\n"
            "2. Main Menu\n"
            "3. Exit"
        )
        return response
    
    else:
        # Invalid input
        hazard_display = session['data'].get('hazard_type', '').replace('_', ' ').title()
        response = (
            f"CON Confirm Report\n"
            f"\n"
            f"Hazard: {hazard_display}\n"
            f"\n"
            f"1. Confirm & Submit\n"
            f"0. Cancel"
        )
        return response


# Test/Demo view for development
@csrf_exempt
@require_http_methods(["GET"])
def ussd_test(request):
    """
    Test USSD flow without real Africa's Talking integration.
    
    Usage:
    /ussd/test/?phone=%2B254712345678&text=1*1
    """
    phone_number = request.GET.get('phone', '+254712345678')
    user_input = request.GET.get('text', '')
    
    # Create mock request
    class MockRequest:
        POST = {
            'sessionId': 'test-session',
            'phoneNumber': phone_number,
            'text': user_input,
            'serviceCode': 'test'
        }
    
    response = ussd_webhook(MockRequest())
    
    return JsonResponse({
        'phone': phone_number,
        'input': user_input,
        'response': response.content.decode()
    })
