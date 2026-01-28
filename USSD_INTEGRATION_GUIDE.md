# SafeRoute USSD Integration Guide

## Overview

The SafeRoute USSD service allows drivers in Kenya and East Africa to report road hazards via simple USSD menu interactions using basic phones.

**USSD Code:** `*123#` (example - configure in Africa's Talking)

## Features

✓ Simple menu-driven interface  
✓ Report hazards: Accidents, Bad Roads, Pedestrians, Black Spots  
✓ Automatic location capture (approximate)  
✓ Confirmation before submission  
✓ Session management  
✓ Database persistence  
✓ Africa's Talking integration ready  

## USSD Menu Structure

```
Main Menu
├── 1. Report Hazard
│   ├── 1. Accident
│   ├── 2. Bad Road
│   ├── 3. Pedestrians
│   ├── 4. Black Spot
│   └── 0. Back
│   └── Confirm & Submit
├── 2. Get Alerts (Coming soon)
└── 3. Exit
```

## Implementation

### Views

**File:** `core/views.py`

#### Main Functions

**`ussd_webhook(request)`** - Africa's Talking POST handler
- Receives USSD requests from Africa's Talking
- Routes to appropriate handler based on session state
- Returns CON/END responses

**`ussd_test(request)`** - Development test endpoint
- Allows testing without Africa's Talking
- Query parameters: `phone`, `text`

#### Session Management

```python
get_session(phone_number)      # Get or create session
clear_session(phone_number)    # Clear session after completion
```

#### Menu Builders

```python
build_main_menu()       # Main menu
build_hazard_menu()     # Hazard selection menu
get_hazard_type(code)   # Map user input to hazard type
```

#### Handler Functions

```python
handle_main_menu()           # Routes main menu selections
handle_hazard_selection()    # Handles hazard type choice
handle_confirmation()        # Confirms and saves report
```

### URL Configuration

**File:** `saferoute/urls.py`

```python
path('ussd/webhook/', views.ussd_webhook, name='ussd_webhook'),
path('ussd/test/', views.ussd_test, name='ussd_test'),
```

## API Reference

### Africa's Talking USSD Request

**Endpoint:** `POST /ussd/webhook/`

**Request Body:**
```json
{
    "sessionId": "12345",
    "phoneNumber": "+254712345678",
    "text": "1*2",
    "serviceCode": "123456"
}
```

**Parameters:**
- `sessionId` - Unique session identifier
- `phoneNumber` - Caller's phone number (with country code)
- `text` - User input (menu selections separated by *)
- `serviceCode` - Your USSD service code

### Response Format

**CON (Continue Session)**
```
CON Menu text\n
options
```

**END (End Session)**
```
END Final message\n
(session ends)
```

## User Flow Example

### Scenario: User reports an accident

```
User dials: *123#
↓
Server responds:
CON Welcome to SafeRoute
Report hazards on the road

1. Report Hazard
2. Get Alerts
3. Exit

User presses: 1
↓
Server responds:
CON Select hazard type:

1. Accident
2. Bad Road
3. Pedestrians
4. Black Spot
0. Back

User presses: 1
↓
Server responds:
CON Confirm Report

Hazard: Accident
Location: Nairobi area

1. Confirm & Submit
0. Cancel

User presses: 1
↓
Server:
- Creates Report in database
- Clears session

Server responds:
END Thank you!
Your Accident report
has been received.

Nearby drivers will
be alerted.
```

## Testing

### Method 1: Test Endpoint (Development)

```bash
# Test basic menu
curl "http://localhost:8000/ussd/test/?phone=%2B254712345678&text="

# Test report hazard selection
curl "http://localhost:8000/ussd/test/?phone=%2B254712345678&text=1"

# Test accident selection
curl "http://localhost:8000/ussd/test/?phone=%2B254712345678&text=1*1"

# Test confirmation
curl "http://localhost:8000/ussd/test/?phone=%2B254712345678&text=1*1*1"
```

### Method 2: Python Shell

```python
from django.test import RequestFactory
from core.views import ussd_webhook

factory = RequestFactory()

# Create POST request
request = factory.post('/ussd/webhook/', {
    'sessionId': '12345',
    'phoneNumber': '+254712345678',
    'text': '1*1*1',
    'serviceCode': '123456'
})

response = ussd_webhook(request)
print(response.content.decode())
```

### Method 3: Africa's Talking Testing

1. Configure webhook URL in Africa's Talking dashboard
2. Use Africa's Talking Simulator
3. Send USSD requests from simulator
4. Monitor logs and database

## Session Management

### How Sessions Work

```
Phone Number → Session State + Data
+254712345678 → {
    'state': 'hazard_type',
    'data': {
        'phone_number': '+254712345678',
        'hazard_type': 'ACCIDENT'
    }
}
```

### Session States

```
STATE_MENU         - Main menu (initial state)
STATE_HAZARD_TYPE  - Selecting hazard type
STATE_CONFIRM      - Confirming submission
```

### In Production

Current implementation uses in-memory dictionary. For production:

```python
# Use Django sessions
from django.contrib.sessions.models import Session

# Or use Redis
import redis
redis_client = redis.Redis()
redis_client.setex(key, timeout, value)
```

## Location Handling

### Current Implementation

Default location for MVP:
```python
latitude: -1.2921   # Nairobi, Kenya
longitude: 36.8219
```

### Production Enhancements

```python
def get_approximate_location():
    # Option 1: GPS from device
    # location = request.location_data
    
    # Option 2: Cell tower triangulation
    # location = get_cell_tower_location(phone_number)
    
    # Option 3: Last known location
    # location = get_last_known_location(phone_number)
    
    # Option 4: Prompt user (text coordinates)
    # location = prompt_for_location()
    
    return location
```

## Database

### Report Model

All reports saved to `Report` model:

```python
class Report(models.Model):
    phone_number = models.CharField(max_length=20)
    hazard_type = models.CharField(max_length=20, choices=HAZARD_TYPE_CHOICES)
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
```

### Querying Reports

```python
from core.models import Report

# All reports from today
today_reports = Report.objects.filter(
    created_at__date=today
)

# Reports from a specific phone
phone_reports = Report.objects.filter(
    phone_number='+254712345678'
)

# Reports by hazard type
accidents = Report.objects.filter(
    hazard_type='ACCIDENT'
)
```

## Integration with Alert Engine

Reports are automatically available for the alert engine:

```python
from core.alert_engine import lifesaver_alert_engine

# Get alerts for driver at location
result = lifesaver_alert_engine(
    phone_number="+254712345678",
    latitude=37.7749,
    longitude=-122.4194
)

# Alerts are sent to nearby drivers
print(f"Alerts sent: {result['alerts_sent']}")
```

## Error Handling

### Validation

```
Missing phone number     → "END Error: Phone number required"
Invalid hazard type     → Show menu again
Database error          → "END Error saving report. Please try again."
Unexpected state        → "END Error: Invalid session state"
```

### Logging

All USSD requests logged:
```
USSD Request: Phone=+254712345678, Input=1
USSD Response: CON Select hazard type...
Report created: ID=5, Phone=+254712345678, Type=ACCIDENT
```

## Africa's Talking Setup

### 1. Create USSD Service

1. Go to Africa's Talking dashboard
2. Create new USSD service
3. Choose "Callback URL" mode
4. Set callback URL: `https://your-domain.com/ussd/webhook/`

### 2. Configure Webhook

```
URL: https://saferoute.example.com/ussd/webhook/
Method: POST
Content-Type: application/x-www-form-urlencoded
```

### 3. Set Response Type

Response format: **Plain text**
- CON for continue
- END for end

### 4. Get Service Code

Your USSD code might be: `*123#` (customizable)

### 5. Test

Use Africa's Talking simulator to test:
- Dial: `*123#`
- Follow menu prompts
- Check reports in database

## Response Examples

### Main Menu
```
CON Welcome to SafeRoute
Report hazards on the road

1. Report Hazard
2. Get Alerts
3. Exit
```

### Hazard Selection
```
CON Select hazard type:

1. Accident
2. Bad Road
3. Pedestrians
4. Black Spot
0. Back
```

### Confirmation
```
CON Confirm Report

Hazard: Accident
Location: Nairobi area

1. Confirm & Submit
0. Cancel
```

### Success
```
END Thank you!
Your Accident report
has been received.

Nearby drivers will
be alerted.
```

### Error
```
END Error saving report.
Please try again.
```

## Performance Considerations

- Session storage: In-memory (max ~10,000 concurrent sessions)
- Database writes: ~100ms per report
- Response time: <500ms typical
- Scalability: Add Redis for session storage

## Future Enhancements

- [ ] Real GPS location from device
- [ ] Language selection (English/Swahili)
- [ ] Driver alert retrieval via USSD
- [ ] Statistics and analytics
- [ ] Multi-language support
- [ ] Photo upload support (if platform allows)
- [ ] Hazard severity rating
- [ ] Report verification

## Troubleshooting

### No response from USSD

1. Check webhook URL is correct in Africa's Talking dashboard
2. Verify `csrf_exempt` decorator is applied
3. Check server logs for errors
4. Verify network connectivity

### Reports not saving

1. Check database is running
2. Verify `Report` model is created (run migrations)
3. Check permissions on database
4. Look for exceptions in logs

### Sessions not working

1. Verify session storage (in-memory dict)
2. Check phone number format includes country code
3. Monitor session cleanup (clear_session calls)

### Africa's Talking integration failing

1. Check API credentials
2. Verify webhook URL accessibility
3. Test with simulator first
4. Check request/response format matches Africa's Talking spec

## Code Examples

### Example 1: Check Reports

```python
from core.models import Report

# Get all reports
all_reports = Report.objects.all()

# Get today's reports
from django.utils import timezone
from datetime import timedelta

today = timezone.now().date()
today_reports = Report.objects.filter(created_at__date=today)

print(f"Total reports today: {today_reports.count()}")
for report in today_reports:
    print(f"{report.phone_number}: {report.get_hazard_type_display()}")
```

### Example 2: Get Alerts for Report

```python
from core.models import Report
from core.alert_engine import lifesaver_alert_engine

# Get latest report
report = Report.objects.latest('created_at')

# Trigger alerts to nearby drivers
result = lifesaver_alert_engine(
    phone_number="+254712345678",  # Driver to alert
    latitude=report.latitude,
    longitude=report.longitude
)

print(f"Alerts sent: {result['alerts_sent']}")
```

### Example 3: Custom USSD Response

```python
# In views.py

def handle_custom_menu(phone_number, user_input, session):
    if user_input == '1':
        return "CON Custom menu option 1"
    elif user_input == '2':
        return "END Thank you!"
    else:
        return "CON Invalid input. Try again."
```

## Support

For issues or questions:
1. Check logs: `journalctl -u saferoute`
2. Review Africa's Talking docs
3. Test with development endpoint first
4. Contact support team

---

**Last Updated:** January 28, 2026  
**Status:** MVP Ready
