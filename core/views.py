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


# ============================================================================
# DEMO ENDPOINT - FOR HACKATHON DEMONSTRATIONS ONLY
# ============================================================================
# This endpoint simulates a driver approaching hazards and triggers alerts.
# It's intended for live demos and testing without real driver apps.
# ============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def demo_driver_alert(request):
    """
    Demo endpoint: Simulate a driver approaching hazards.
    
    This endpoint demonstrates the complete SafeRoute alert system:
    1. Accept driver location (phone, latitude, longitude)
    2. Find nearby hazards
    3. Trigger LifeSaver alert engine
    4. Return alert results
    
    Perfect for hackathon demos and testing.
    
    POST /demo/driver-alert/
    {
        "phone_number": "+254712345678",
        "latitude": -1.2921,
        "longitude": 36.8219,
        "radius_meters": 300  (optional, default 300)
    }
    
    Response:
    {
        "success": true,
        "driver": {
            "phone": "+254712345678",
            "location": {"latitude": -1.2921, "longitude": 36.8219}
        },
        "hazards_found": 3,
        "hazards_deduped": 2,
        "alerts_sent": 2,
        "hazard_details": [
            {
                "type": "Accident",
                "severity": 5,
                "distance_meters": 85,
                "alert_channel": "VOICE"
            },
            ...
        ],
        "alerts": [
            {
                "hazard_type": "Accident",
                "message": "Critical accident 85m ahead on Uhuru Highway",
                "channel": "VOICE",
                "success": true
            },
            ...
        ]
    }
    """
    try:
        import json
        from core.alert_engine import lifesaver_alert_engine
        from core.models import Hazard
        from core.utils import haversine_distance
        
        # Parse request data
        data = json.loads(request.body)
        phone_number = data.get('phone_number')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        radius_meters = data.get('radius_meters', 300)
        
        # Validate required fields
        if not phone_number or latitude is None or longitude is None:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields: phone_number, latitude, longitude'
            }, status=400)
        
        # Run the alert engine
        logger.info(f"Demo: Driver {phone_number} at ({latitude}, {longitude})")
        result = lifesaver_alert_engine(
            phone_number=phone_number,
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters
        )
        
        # Build detailed hazard information
        hazard_details = []
        for hazard_id in result.get('hazards', []):
            try:
                hazard = Hazard.objects.get(id=hazard_id['id'])
                distance = haversine_distance(
                    latitude, longitude,
                    hazard.latitude, hazard.longitude
                )
                
                # Determine alert channel based on severity
                if hazard.severity >= 4:
                    channel = "VOICE"
                else:
                    channel = "SMS"
                
                hazard_details.append({
                    'id': hazard.id,
                    'type': hazard.get_type_display(),
                    'severity': hazard.severity,
                    'distance_meters': round(distance, 1),
                    'location': {
                        'latitude': hazard.latitude,
                        'longitude': hazard.longitude
                    },
                    'alert_channel': channel,
                    'created_at': hazard.created_at.isoformat()
                })
            except Hazard.DoesNotExist:
                pass
        
        # Build response
        response_data = {
            'success': result.get('success', True),
            'driver': {
                'phone': phone_number,
                'location': {
                    'latitude': latitude,
                    'longitude': longitude
                }
            },
            'search_radius_meters': radius_meters,
            'hazards_found': result.get('nearby_hazards', 0),
            'hazards_deduplicated': result.get('deduplicated', 0),
            'alerts_sent': result.get('alerts_sent', 0),
            'hazard_details': hazard_details,
            'alerts': result.get('alerts', []),
            'demo_note': 'This is a demo endpoint for hackathon demonstrations'
        }
        
        logger.info(f"Demo: {response_data['alerts_sent']} alerts sent to {phone_number}")
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        logger.error(f"Demo endpoint error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def demo_driver_alert_ui(request):
    """
    Simple HTML UI for testing the demo driver alert endpoint.
    
    Allows you to input driver details and see alerts in real-time.
    
    Usage: GET /demo/driver-alert-ui/
    """
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SafeRoute Demo - Driver Alert Simulation</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                max-width: 600px;
                width: 100%;
                padding: 40px;
            }
            h1 {
                color: #333;
                margin-bottom: 10px;
                font-size: 24px;
            }
            .subtitle {
                color: #666;
                margin-bottom: 30px;
                font-size: 14px;
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                color: #333;
                font-weight: 500;
                font-size: 14px;
            }
            input {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            .button-group {
                display: flex;
                gap: 10px;
                margin-top: 30px;
            }
            button {
                flex: 1;
                padding: 12px;
                font-size: 14px;
                font-weight: 600;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                transition: all 0.3s;
            }
            .btn-submit {
                background: #667eea;
                color: white;
            }
            .btn-submit:hover {
                background: #5568d3;
            }
            .btn-submit:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            .btn-reset {
                background: #f0f0f0;
                color: #333;
            }
            .btn-reset:hover {
                background: #e0e0e0;
            }
            .loading {
                display: none;
                text-align: center;
                color: #667eea;
                font-size: 14px;
            }
            .results {
                margin-top: 30px;
                padding: 20px;
                background: #f9f9f9;
                border-radius: 5px;
                display: none;
            }
            .results.show {
                display: block;
            }
            .result-header {
                color: #333;
                font-weight: 600;
                margin-bottom: 15px;
                font-size: 16px;
            }
            .alert-item {
                background: white;
                padding: 15px;
                margin-bottom: 10px;
                border-left: 4px solid #667eea;
                border-radius: 3px;
                font-size: 14px;
            }
            .alert-success {
                border-left-color: #4caf50;
            }
            .alert-warning {
                border-left-color: #ff9800;
            }
            .alert-error {
                border-left-color: #f44336;
                color: #f44336;
            }
            .alert-type {
                font-weight: 600;
                color: #333;
                margin-bottom: 5px;
            }
            .alert-channel {
                display: inline-block;
                padding: 3px 8px;
                background: #667eea;
                color: white;
                border-radius: 3px;
                font-size: 12px;
                margin-top: 5px;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 15px;
                margin-bottom: 20px;
            }
            .stat {
                background: white;
                padding: 15px;
                border-radius: 5px;
                text-align: center;
            }
            .stat-value {
                font-size: 24px;
                font-weight: 600;
                color: #667eea;
            }
            .stat-label {
                font-size: 12px;
                color: #666;
                margin-top: 5px;
            }
            .examples {
                background: #f0f4ff;
                border: 1px solid #cce0ff;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 20px;
                font-size: 13px;
                color: #333;
            }
            .examples-title {
                font-weight: 600;
                margin-bottom: 10px;
                color: #667eea;
            }
            .example-btn {
                background: #e0e7ff;
                color: #667eea;
                padding: 8px 12px;
                border-radius: 3px;
                margin-top: 10px;
                cursor: pointer;
                font-size: 12px;
                display: inline-block;
                font-weight: 500;
                border: 1px solid #cce0ff;
            }
            .example-btn:hover {
                background: #cce0ff;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚗 SafeRoute Demo</h1>
            <p class="subtitle">Simulate a driver approaching hazards and trigger live alerts</p>
            
            <div class="examples">
                <div class="examples-title">Quick Examples:</div>
                <button class="example-btn" onclick="useExample('nairobi')">Nairobi Center</button>
                <button class="example-btn" onclick="useExample('accident')">Near Accident</button>
                <button class="example-btn" onclick="useExample('empty')">Empty Area</button>
            </div>
            
            <form id="demoForm">
                <div class="form-group">
                    <label for="phone">📱 Driver Phone Number</label>
                    <input type="text" id="phone" name="phone" value="+254712999999" required>
                </div>
                
                <div class="form-group">
                    <label for="latitude">📍 Latitude</label>
                    <input type="number" id="latitude" name="latitude" value="-1.2921" step="0.0001" required>
                </div>
                
                <div class="form-group">
                    <label for="longitude">📍 Longitude</label>
                    <input type="number" id="longitude" name="longitude" value="36.8219" step="0.0001" required>
                </div>
                
                <div class="form-group">
                    <label for="radius">⭕ Search Radius (meters)</label>
                    <input type="number" id="radius" name="radius" value="300" min="50" max="1000">
                </div>
                
                <div class="button-group">
                    <button type="submit" class="btn-submit">🔍 Simulate Driver Alert</button>
                    <button type="reset" class="btn-reset">↻ Reset</button>
                </div>
                
                <div class="loading" id="loading">Processing...</div>
            </form>
            
            <div class="results" id="results">
                <div class="result-header">⚠️ Alert Results</div>
                <div class="stats">
                    <div class="stat">
                        <div class="stat-value" id="hazardsFound">0</div>
                        <div class="stat-label">Hazards Found</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" id="hazardsDedup">0</div>
                        <div class="stat-label">After Dedup</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" id="alertsSent">0</div>
                        <div class="stat-label">Alerts Sent</div>
                    </div>
                </div>
                <div id="alertsList"></div>
            </div>
        </div>
        
        <script>
        function useExample(type) {
            const examples = {
                nairobi: { phone: '+254712345678', lat: -1.2921, lon: 36.8219 },
                accident: { phone: '+254712345678', lat: -1.2920, lon: 36.8218 },
                empty: { phone: '+254712345678', lat: -1.3, lon: 36.9 }
            };
            const ex = examples[type];
            if (ex) {
                document.getElementById('phone').value = ex.phone;
                document.getElementById('latitude').value = ex.lat;
                document.getElementById('longitude').value = ex.lon;
            }
        }
        
        document.getElementById('demoForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const form = e.target;
            const submitBtn = form.querySelector('.btn-submit');
            const loading = document.getElementById('loading');
            
            const data = {
                phone_number: document.getElementById('phone').value,
                latitude: parseFloat(document.getElementById('latitude').value),
                longitude: parseFloat(document.getElementById('longitude').value),
                radius_meters: parseInt(document.getElementById('radius').value)
            };
            
            submitBtn.disabled = true;
            loading.style.display = 'block';
            
            try {
                const response = await fetch('/demo/driver-alert/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                document.getElementById('hazardsFound').textContent = result.hazards_found;
                document.getElementById('hazardsDedup').textContent = result.hazards_deduplicated;
                document.getElementById('alertsSent').textContent = result.alerts_sent;
                
                const alertsList = document.getElementById('alertsList');
                alertsList.innerHTML = '';
                
                if (result.hazard_details && result.hazard_details.length > 0) {
                    result.hazard_details.forEach(hazard => {
                        const div = document.createElement('div');
                        div.className = `alert-item alert-success`;
                        div.innerHTML = `
                            <div class="alert-type">📍 ${hazard.type} (${hazard.distance_meters}m away)</div>
                            <div>Severity: ${hazard.severity}/5</div>
                            <div>Location: ${hazard.location.latitude.toFixed(4)}, ${hazard.location.longitude.toFixed(4)}</div>
                            <span class="alert-channel">${hazard.alert_channel}</span>
                        `;
                        alertsList.appendChild(div);
                    });
                } else {
                    const div = document.createElement('div');
                    div.className = 'alert-item';
                    div.innerHTML = '<em>No hazards found in this area</em>';
                    alertsList.appendChild(div);
                }
                
                document.getElementById('results').classList.add('show');
                
            } catch (error) {
                alert('Error: ' + error.message);
            } finally {
                submitBtn.disabled = false;
                loading.style.display = 'none';
            }
        });
        </script>
    </body>
    </html>
    """
    
    return HttpResponse(html, content_type='text/html')
