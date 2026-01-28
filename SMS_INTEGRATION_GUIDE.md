# Africa's Talking SMS & Voice Integration Guide

## Overview

SafeRoute integrates with Africa's Talking to send real-time alerts to drivers about hazards:
- **SMS** - Text message alerts
- **Voice** - Phone calls with text-to-speech

**Default SMS Message:**
```
⚠️ LifeSaver Alert: Dangerous road section ahead. Please slow down.
```

**Default Voice Message:**
```
LifeSaver Alert. Dangerous road section ahead. Reduce speed.
```

## Setup Instructions

### 1. Install Required Package

```bash
pip install africastalking
```

### 2. Get Africa's Talking Credentials

1. Create an account at [Africa's Talking](https://africastalking.com)
2. Get your API Key from the dashboard
3. Note your username

### 3. Configure Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
AT_USERNAME=your_africastalking_username
AT_API_KEY=your_africastalking_api_key
```

### 4. Install python-dotenv (Optional but Recommended)

```bash
pip install python-dotenv
```

Then in your Django settings or manage.py, load environment variables:

```python
from dotenv import load_dotenv
load_dotenv()
```

## API Functions

### 1. `send_sms_alert(phone_number, custom_message=None)`

Send a single SMS alert.

```python
from core.utils import send_sms_alert

# Send default SafeRoute alert
success, message = send_sms_alert("+254712345678")

# Send custom message
success, message = send_sms_alert("+254712345678", "Custom alert message")

if success:
    print("SMS sent successfully")
else:
    print(f"Error: {message}")
```

**Parameters:**
- `phone_number` (str): Recipient phone with country code (e.g., +254712345678)
- `custom_message` (str, optional): Custom message. Uses default if None.

**Returns:**
- `(success: bool, message: str)`

### 2. `send_sms_alert_with_fatigue_check(phone_number, hazard, custom_message=None)`

Send SMS with alert fatigue prevention (max once per 30 minutes).

```python
from core.utils import send_sms_alert_with_fatigue_check
from core.models import Hazard

hazard = Hazard.objects.get(id=1)
success, message = send_sms_alert_with_fatigue_check(
    "+254712345678",
    hazard,
    custom_message="Accident ahead!"
)

if success:
    print("Alert sent")
else:
    print(f"Alert blocked or failed: {message}")
```

**Parameters:**
- `phone_number` (str): Recipient phone with country code
- `hazard` (Hazard): The hazard instance
- `custom_message` (str, optional): Custom message

**Returns:**
- `(success: bool, message: str)`

### 3. `get_africastalking_client()`

Get the SMS client (for advanced usage).

```python
from core.utils import get_africastalking_client

sms = get_africastalking_client()
if sms:
    response = sms.send("Message", ["+254712345678"])
else:
    print("Credentials not configured")
```

## Voice Call API

### 1. `make_voice_call(phone_number, message=None)`

Make an outbound voice call with text-to-speech message.

```python
from core.utils import make_voice_call

# Send default voice alert
success, message = make_voice_call("+254712345678")

# Send custom voice message
success, message = make_voice_call(
    "+254712345678", 
    "Alert. Accident ahead. Reduce speed immediately."
)

if success:
    print("Voice call initiated")
else:
    print(f"Error: {message}")
```

**Parameters:**
- `phone_number` (str): Recipient phone with country code
- `message` (str, optional): TTS message. Uses default if None.

**Returns:**
- `(success: bool, message: str)`

### 2. `send_voice_alert_with_fallback(phone_number, hazard, voice_message=None, sms_message=None)`

Send voice alert with automatic SMS fallback if voice fails.

```python
from core.utils import send_voice_alert_with_fallback
from core.models import Hazard

hazard = Hazard.objects.get(id=1)

# Try voice call, fallback to SMS
success, voice_response, sms_response = send_voice_alert_with_fallback(
    "+254712345678",
    hazard,
    voice_message="Critical hazard ahead.",
    sms_message="🚨 CRITICAL HAZARD"
)

if success:
    if sms_response:
        print(f"SMS fallback sent: {sms_response}")
    else:
        print("Voice call initiated successfully")
```

**Parameters:**
- `phone_number` (str): Recipient phone
- `hazard` (Hazard): The hazard instance
- `voice_message` (str, optional): Custom voice message
- `sms_message` (str, optional): Fallback SMS message

**Returns:**
- `(success: bool, voice_response: str, sms_response: str)`

**Features:**
- Tries voice call first (more urgent)
- Falls back to SMS if voice fails
- Includes alert fatigue prevention
- Returns details about what was sent

## Testing Locally

### Test Without Credentials

```bash
python manage.py shell
```

```python
from core.utils import send_sms_alert

success, message = send_sms_alert("+254712345678")
print(success)  # False
print(message)  # "Africa's Talking credentials not configured..."
```

### Test With Mock Credentials

Set environment variables:

```bash
export AT_USERNAME=test_username
export AT_API_KEY=test_api_key
python manage.py shell
```

```python
from core.utils import send_sms_alert

# Will attempt to send (may fail if credentials invalid)
success, message = send_sms_alert("+254712345678")
print(message)  # Response from API or error
```

### Run Complete Test Suite

```bash
python manage.py shell
```

```python
from core.sms_tests import run_all_tests
run_all_tests()
```

Or from command line:

```bash
python manage.py shell < core/sms_tests.py
```

## Usage in Views

Example view to send alerts when a hazard is detected:

```python
from django.http import JsonResponse
from core.models import Hazard
from core.utils import send_sms_alert_with_fatigue_check

def alert_drivers(request):
    hazard_id = request.POST.get('hazard_id')
    phone_number = request.POST.get('phone')
    
    hazard = Hazard.objects.get(id=hazard_id)
    success, message = send_sms_alert_with_fatigue_check(phone_number, hazard)
    
    return JsonResponse({
        'success': success,
        'message': message
    })
```

## Error Handling

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| "Credentials not configured" | Missing env vars | Set `AT_USERNAME` and `AT_API_KEY` |
| "SMS delivery failed" | Invalid phone number | Use format: +[country_code][number] |
| "ImportError: No module named africastalking" | Package not installed | `pip install africastalking` |
| "No recipients in response" | API error | Check Africa's Talking dashboard |

## Best Practices

1. **Always use fatigue check** - Prevents alert spam
   ```python
   send_sms_alert_with_fatigue_check(phone, hazard)  # ✓ Good
   send_sms_alert(phone)  # ✗ Avoid
   ```

2. **Validate phone numbers** - Ensure country code included
   ```python
   # ✓ Correct
   send_sms_alert("+254712345678")
   
   # ✗ Incorrect
   send_sms_alert("712345678")
   ```

3. **Keep messages short** - SMS has character limits
   ```python
   # ✓ Good (67 chars)
   "⚠️ LifeSaver Alert: Dangerous road section ahead. Please slow down."
   
   # ✗ Too long (will be split)
   "This is a very long message that will exceed SMS limits and cost more..."
   ```

4. **Log alerts** - AlertLog records all sent alerts
   ```python
   from core.models import AlertLog
   recent = AlertLog.objects.filter(sent_at__gte=...)
   ```

## Pricing

Africa's Talking charges per SMS sent. Check their pricing in your dashboard.

## Security Notes

- Never commit `.env` file with credentials to git
- Add `.env` to `.gitignore`
- Rotate API keys periodically
- Use environment variables, not hardcoded credentials
