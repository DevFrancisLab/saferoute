# SafeRoute Quick Start Guide

**Get up and running in 5 minutes**

---

## Prerequisites

- Python 3.8+
- Django 5.2.5
- SQLite (included with Python)
- Africa's Talking account (optional for MVP)

---

## Installation

```bash
# Navigate to project
cd /home/frank/saferoute

# Create virtual environment (if needed)
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install django

# Run migrations
python manage.py migrate

# Create superuser (optional, for admin panel)
python manage.py createsuperuser
```

---

## Quick Test

### 1. Test USSD Hazard Reporting

```bash
python manage.py shell << 'EOF'
from django.test import RequestFactory
from core.views import ussd_webhook

factory = RequestFactory()

# Simulate complete USSD flow
phone = '+254712345678'

# Step 1: Initial menu
req = factory.post('/ussd/webhook/', {
    'sessionId': 'test123',
    'phoneNumber': phone,
    'text': '',
    'serviceCode': '123456'
})
response = ussd_webhook(req)
print("Menu:", response.content.decode()[:50])

# Step 2: Report hazard
req = factory.post('/ussd/webhook/', {
    'sessionId': 'test123',
    'phoneNumber': phone,
    'text': '1',
    'serviceCode': '123456'
})
response = ussd_webhook(req)
print("Hazard Types:", response.content.decode()[:50])

# Step 3: Select Accident
req = factory.post('/ussd/webhook/', {
    'sessionId': 'test123',
    'phoneNumber': phone,
    'text': '1*1',
    'serviceCode': '123456'
})
response = ussd_webhook(req)
print("Confirm:", response.content.decode()[:50])

# Step 4: Confirm report
req = factory.post('/ussd/webhook/', {
    'sessionId': 'test123',
    'phoneNumber': phone,
    'text': '1*1*1',
    'serviceCode': '123456'
})
response = ussd_webhook(req)
print("Success:", response.content.decode()[:50])

# Check database
from core.models import Report
reports = Report.objects.all()
print(f"\nReports in database: {reports.count()}")
for r in reports:
    print(f"  • {r.phone_number}: {r.get_hazard_type_display()}")
EOF
```

### 2. Test Alert Engine

```bash
python manage.py shell << 'EOF'
from core.models import Hazard
from core.alert_engine import lifesaver_alert_engine

# Create test hazard
hazard = Hazard.objects.create(
    type='ACCIDENT',
    severity=5,
    latitude=-1.2921,
    longitude=36.8219
)

# Run alert engine
result = lifesaver_alert_engine(
    phone_number='+254712999999',
    latitude=-1.2921,
    longitude=36.8219
)

print(f"Hazards found: {result['nearby_hazards']}")
print(f"Alerts sent: {result['alerts_sent']}")
print(f"Success: {result['success']}")
EOF
```

### 3. Test Distance Calculation

```bash
python manage.py shell << 'EOF'
from core.utils import haversine_distance

# Same location
d1 = haversine_distance(-1.2921, 36.8219, -1.2921, 36.8219)
print(f"Same location: {d1:.0f}m (expect 0m)")

# 50 meters apart
d2 = haversine_distance(-1.2921, 36.8219, -1.2925, 36.8220)
print(f"50m apart: {d2:.0f}m (expect ~50m)")

# Verify accuracy
assert d1 < 1
assert 45 < d2 < 55
print("✓ Distance calculations accurate")
EOF
```

---

## API Reference

### Create a Hazard

```python
from core.models import Hazard

hazard = Hazard.objects.create(
    type='ACCIDENT',  # ACCIDENT, BAD_ROAD, PEDESTRIANS, BLACKSPOT
    severity=5,       # 1-5 (1=minor, 5=critical)
    latitude=-1.2921,
    longitude=36.8219
)
```

### Find Nearby Hazards

```python
from core.alert_engine import LifeSaverAlertEngine

engine = LifeSaverAlertEngine(
    phone_number="+254712345678",
    latitude=-1.2921,
    longitude=36.8219,
    radius_meters=300
)

result = engine.process_alerts()
print(f"Found {result['nearby_hazards']} hazards")
```

### Check Alert Fatigue

```python
from core.utils import has_recent_alert

# Check if alert sent in last 30 minutes
has_alert = has_recent_alert(
    phone_number="+254712345678",
    hazard_id=1
)

if not has_alert:
    # Safe to send alert
    print("Sending alert...")
```

### Send SMS Alert

```python
from core.utils import send_sms_alert_with_fatigue_check

success, message = send_sms_alert_with_fatigue_check(
    phone_number="+254712345678",
    hazard_type="ACCIDENT",
    severity=5
)

print(f"Success: {success}")
print(f"Message: {message}")
```

---

## Configuration

### Environment Variables

Create `.env` file (optional):

```bash
AT_USERNAME=your_username
AT_API_KEY=your_api_key
```

Without these, SMS/Voice features will return test responses.

### Django Settings

Modify `saferoute/settings.py` to customize:

```python
# Alert Engine Settings
DEFAULT_RADIUS_METERS = 300  # Search radius
SEVERITY_THRESHOLD = 2        # Minimum severity to alert
ALERT_COOLDOWN_MINUTES = 30   # Fatigue prevention window
DEDUP_DISTANCE_METERS = 50    # Deduplication radius
```

---

## File Structure

```
saferoute/
├── core/
│   ├── models.py              # Hazard, Report, AlertLog
│   ├── views.py               # USSD webhook
│   ├── utils.py               # Utility functions
│   ├── alert_engine.py        # Main alert service
│   ├── admin.py               # Django admin
│   └── migrations/            # Database migrations
│
├── saferoute/
│   ├── settings.py            # Django config
│   ├── urls.py                # URL routing
│   ├── wsgi.py                # WSGI app
│   └── asgi.py                # ASGI app
│
├── manage.py                  # Django CLI
├── db.sqlite3                 # SQLite database
├── TEST_REPORT.md             # Full test results
├── SAFEROUTE_COMPLETE.md      # Complete documentation
└── QUICK_START.md             # This file
```

---

## Common Tasks

### View All Hazards

```bash
python manage.py shell << 'EOF'
from core.models import Hazard

for h in Hazard.objects.all():
    print(f"{h.get_type_display()} (Severity {h.severity}) at ({h.latitude}, {h.longitude})")
EOF
```

### View All Reports

```bash
python manage.py shell << 'EOF'
from core.models import Report

for r in Report.objects.all():
    print(f"{r.phone_number}: {r.get_hazard_type_display()}")
EOF
```

### View Alert History

```bash
python manage.py shell << 'EOF'
from core.models import AlertLog

for a in AlertLog.objects.all():
    print(f"Alert to {a.phone_number} via {a.get_channel_display()}")
EOF
```

### Clear Database (Dev Only)

```bash
python manage.py shell << 'EOF'
from core.models import Hazard, Report, AlertLog

Hazard.objects.all().delete()
Report.objects.all().delete()
AlertLog.objects.all().delete()

print("Database cleared")
EOF
```

---

## Testing URLs

### USSD Test Endpoint

Test without Africa's Talking:

```
http://localhost:8000/ussd/test/?phone=%2B254712345678&text=1*1*1
```

Response:
```json
{
    "phone": "+254712345678",
    "input": "1*1*1",
    "response": "END Thank you!\nYour Accident report\nhas been received."
}
```

### Admin Panel

```
http://localhost:8000/admin/
```

Requires superuser account created via:
```bash
python manage.py createsuperuser
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Database Locked

```bash
# Delete and recreate database
rm db.sqlite3
python manage.py migrate
```

### Import Errors

```bash
# Reinstall Django
pip install --upgrade django
```

### USSD Not Working

1. Check phone number format (must include country code)
2. Verify Africa's Talking credentials in .env
3. Test via `/ussd/test/` endpoint first

---

## Performance Tips

### For 1000+ Users

1. Migrate to PostgreSQL
   ```bash
   pip install psycopg2
   # Update settings.py DATABASES config
   ```

2. Add database indexes
   ```python
   # In models.py
   class Meta:
       indexes = [
           models.Index(fields=['phone_number']),
           models.Index(fields=['latitude', 'longitude']),
       ]
   ```

3. Use Redis for sessions
   ```bash
   pip install redis
   # Update SESSION_ENGINE in settings.py
   ```

4. Enable caching
   ```python
   CACHES = {
       'default': {
           'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
       }
   }
   ```

---

## Next Steps

1. **Setup Africa's Talking**
   - Create account at [africatalking.com](https://africatalking.com)
   - Get API credentials
   - Add to `.env` file

2. **Deploy to Server**
   - Set up web server (Gunicorn)
   - Configure reverse proxy (Nginx)
   - Enable HTTPS

3. **Monitor in Production**
   - Check AlertLog table regularly
   - Monitor API response times
   - Track alert delivery success rates

4. **Gather User Feedback**
   - Survey drivers on alert usefulness
   - Collect hazard type corrections
   - Iterate on alert messaging

---

## Support

For issues:

1. Check `TEST_REPORT.md` for known issues
2. Review `SAFEROUTE_COMPLETE.md` for detailed docs
3. Check logs: `AlertLog.objects.all()`
4. Test components individually in Django shell

---

## Example Use Cases

### Scenario 1: Report Accident via USSD

```
User: +254712345678
Menu: 1 (Report) > 1 (Accident) > 1 (Confirm)
Result: Report saved, alerts sent to nearby drivers
```

### Scenario 2: Multiple Hazards

```
Setup:
  Driver at (-1.2921, 36.8219)
  Hazard 1: Accident (sev 5) 16m away
  Hazard 2: Bad Road (sev 3) 46m away
  
Result:
  Alert 1: VOICE call "Accident ahead"
  Alert 2: SMS "Bad road reported"
```

### Scenario 3: Alert Fatigue Prevention

```
01:00 PM: Alert sent → AlertLog created
01:15 PM: Same hazard active → NO alert (within 30m)
01:35 PM: 35 minutes later → Safe to alert again
```

---

## License & Credits

SafeRoute MVP - Built for Road Safety Hackathon

Technologies:
- Django 5.2.5
- Africa's Talking APIs
- Haversine Distance Algorithm
- SQLite Database

---

**Last Updated:** 2026-01-28  
**Version:** 1.0  
**Status:** Production Ready
