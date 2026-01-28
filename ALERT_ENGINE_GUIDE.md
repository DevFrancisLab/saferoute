# LifeSaver Alert Engine Documentation

## Overview

The **LifeSaver Alert Engine** is the core alert service for SafeRoute. It:
1. Finds hazards within a specified radius
2. Deduplicates nearby hazards
3. Prioritizes alerts by severity
4. Sends voice or SMS alerts automatically
5. Tracks all alert attempts

## Quick Start

### Basic Usage

```python
from core.alert_engine import lifesaver_alert_engine

result = lifesaver_alert_engine(
    phone_number="+254712345678",
    latitude=37.7749,
    longitude=-122.4194,
    radius_meters=300
)

print(f"Alerts sent: {result['alerts_sent']}")
```

### Response Format

```json
{
    "success": true,
    "nearby_hazards": 3,
    "deduplicated": 2,
    "alerts_sent": 2,
    "hazards": [
        {
            "id": 1,
            "type": "Accident",
            "severity": 5,
            "lat": 37.7750,
            "lng": -122.4194
        }
    ],
    "alerts": [
        {
            "hazard_id": 1,
            "hazard_type": "Accident",
            "severity": 5,
            "success": true,
            "message": "VOICE CALL: Alert initiated..."
        }
    ]
}
```

## Features

### 1. Radius-Based Search
- Searches for hazards within specified radius (default: 300m)
- Returns closest hazards first
- Configurable radius for different scenarios

### 2. Intelligent Deduplication
**Problem:** Multiple reports of same hazard create alert spam

**Solution:** Deduplication rules
```
For each hazard type:
  1. Group hazards by type
  2. Hazards within 50m = duplicate
  3. Keep highest severity version
  4. Keep most recently created
```

**Example:**
```
Input: 4 nearby hazards
  • Accident (Severity 5)
  • Accident (Severity 3) - 20m away, duplicate!
  • Black Spot (Severity 3)
  • Pedestrians (Severity 4) - too far, not included
  
Output: 2 deduplicated hazards
  • Accident (Severity 5) - kept higher severity
  • Black Spot (Severity 3)
```

### 3. Severity-Based Alerts
```
Severity 1-2: NO ALERT (below threshold)
Severity 3:   SMS ALERT (normal)
Severity 4-5: VOICE ALERT (urgent)
              + Auto SMS fallback if voice fails
```

### 4. Multi-Channel Delivery
- **Voice** for critical hazards (immediate, real-time)
- **SMS** for normal hazards (reliable, documented)
- **Automatic fallback** from voice to SMS

### 5. Alert Fatigue Prevention
- 30-minute cooldown per phone + hazard + channel
- Prevents driver from receiving duplicate alerts
- Tracked in AlertLog database

## API Reference

### `lifesaver_alert_engine(phone_number, latitude, longitude, radius_meters=300)`

Main entry point - single function for production use.

**Parameters:**
```python
phone_number: str        # Driver's phone (+254712345678)
latitude: float          # Driver's current latitude
longitude: float         # Driver's current longitude
radius_meters: int       # Search radius in meters (default: 300)
```

**Returns:**
```python
{
    'success': bool,          # Processing succeeded
    'nearby_hazards': int,    # Found in radius
    'deduplicated': int,      # After dedup
    'alerts_sent': int,       # Number of alerts sent
    'hazards': [...],         # Hazards to alert about
    'alerts': [...]           # Alert attempt details
}
```

**Example:**
```python
from core.alert_engine import lifesaver_alert_engine

result = lifesaver_alert_engine(
    phone_number="+254712345678",
    latitude=37.7749,
    longitude=-122.4194,
    radius_meters=500  # Search 500m instead of 300m
)

if result['alerts_sent'] > 0:
    for alert in result['alerts']:
        print(f"{alert['hazard_type']}: {alert['message']}")
```

### `LifeSaverAlertEngine` Class

For advanced usage with more control:

```python
from core.alert_engine import LifeSaverAlertEngine

engine = LifeSaverAlertEngine(
    phone_number="+254712345678",
    latitude=37.7749,
    longitude=-122.4194,
    radius_meters=300
)

# Step 1: Find hazards
nearby = engine.find_nearby_hazards()
print(f"Found {len(nearby)} hazards")

# Step 2: Deduplicate
dedup = engine.deduplicate_hazards()
print(f"After dedup: {len(dedup)}")

# Step 3: Filter by severity
filtered = engine.filter_by_severity()
print(f"Meeting severity threshold: {len(filtered)}")

# Step 4: Send alerts
result = engine.process_alerts()
```

## Configuration

### Default Settings

```python
DEFAULT_RADIUS_METERS = 300    # Search area
SEVERITY_THRESHOLD = 2          # Minimum severity to alert
```

### Customization

```python
# Custom radius
result = lifesaver_alert_engine(
    phone_number="+254712345678",
    latitude=37.7749,
    longitude=-122.4194,
    radius_meters=1000  # 1km instead of 300m
)

# Custom severity threshold
engine = LifeSaverAlertEngine(
    phone_number="+254712345678",
    latitude=37.7749,
    longitude=-122.4194
)
engine.SEVERITY_THRESHOLD = 3  # Only alert for 3+
result = engine.process_alerts()
```

## Processing Pipeline

```
Input: phone_number, latitude, longitude, radius_meters
  ↓
Step 1: Find Nearby Hazards
  ├─ Query all hazards in database
  ├─ Calculate distance to each
  └─ Keep only within radius
  
Step 2: Deduplicate
  ├─ Group by hazard type
  ├─ Find clusters (within 50m)
  └─ Keep best from each cluster
  
Step 3: Filter by Severity
  ├─ Remove severity 1-2 (too minor)
  └─ Keep 3+ (alert-worthy)
  
Step 4: Select Alert Channel
  ├─ Severity 4-5 → VOICE + SMS fallback
  └─ Severity 2-3 → SMS
  
Step 5: Send Alerts
  ├─ Check fatigue (30 min cooldown)
  ├─ Send via selected channel
  └─ Log attempt in AlertLog
  
Output: Result dictionary with details
```

## Examples

### Example 1: Basic Alert
```python
result = lifesaver_alert_engine(
    phone_number="+254712345678",
    latitude=37.7749,
    longitude=-122.4194
)

print(f"Sent {result['alerts_sent']} alerts")
```

### Example 2: Check What Happened
```python
result = lifesaver_alert_engine("+254712345678", 37.7749, -122.4194)

print(f"Found {result['nearby_hazards']} hazards")
print(f"Removed {result['nearby_hazards'] - result['deduplicated']} duplicates")
print(f"Sent {result['alerts_sent']} alerts")

for alert in result['alerts']:
    if alert['success']:
        print(f"✓ {alert['hazard_type']} alerted via {alert['message']}")
    else:
        print(f"✗ {alert['hazard_type']} failed: {alert['message']}")
```

### Example 3: Custom Radius
```python
# Different radii for different scenarios
normal = lifesaver_alert_engine(..., radius_meters=300)   # City
highway = lifesaver_alert_engine(..., radius_meters=1000) # Highway
```

### Example 4: Integration with Django View
```python
from django.http import JsonResponse
from core.alert_engine import lifesaver_alert_engine

def trigger_alerts(request):
    phone = request.POST.get('phone')
    lat = float(request.POST.get('lat'))
    lng = float(request.POST.get('lng'))
    
    result = lifesaver_alert_engine(phone, lat, lng)
    
    return JsonResponse(result)
```

## Testing

### Run Demo
```bash
python manage.py shell
>>> from core.alert_engine_demo import run_all_demos
>>> run_all_demos()
```

### Test with Your Data
```bash
python manage.py shell
>>> from core.alert_engine import lifesaver_alert_engine
>>> result = lifesaver_alert_engine("+254712345678", 37.7749, -122.4194)
>>> print(result)
```

## How It Works: Detailed Example

**Scenario:** Driver at (37.7749, -122.4194) with 4 nearby hazards

**Database State:**
```
ID  Type        Severity  Lat      Lng       Distance
1   Accident    5         37.7750  -122.4194 10m
2   Accident    3         37.7752  -122.4196 30m (duplicate!)
3   Black Spot  3         37.7751  -122.4195 15m
4   Pedestrians 4         37.8000  -122.4100 300m
```

**Step 1: Find Within Radius (300m)**
```
Keep: IDs 1, 2, 3
Drop: ID 4 (too far)
Result: 3 hazards
```

**Step 2: Deduplicate**
```
Accident cluster: IDs 1, 2 (both within 50m of each other)
  → Keep ID 1 (higher severity: 5 vs 3)
Black Spot: ID 3 (alone)
  → Keep ID 3

Result: 2 hazards (removed 1 duplicate)
```

**Step 3: Filter by Severity (threshold >= 2)**
```
Keep: Both (3 and 5 meet threshold)
Result: 2 hazards
```

**Step 4: Select Channels**
```
Accident (5) → VOICE (urgent)
Black Spot (3) → SMS (normal)
```

**Step 5: Send Alerts**
```
VOICE call to +254712345678:
  "Alert. Accident ahead. Reduce speed immediately."
  (With SMS fallback if voice fails)

SMS to +254712345678:
  "⚠️ Black Spot: Ahead. Slow down."
```

## Error Handling

All operations are wrapped in try-catch:

```python
# Missing credentials
→ "Africa's Talking credentials not configured..."

# Invalid phone number
→ API error message

# Database error
→ Exception details

# All returned in result['alerts'][i]['message']
```

## Performance Notes

- **Radius Search:** O(n) where n = total hazards in DB
- **Deduplication:** O(m²) where m = hazards in radius (typically <10)
- **Alert Sending:** Synchronous (consider async for large numbers)

For 100 hazards in DB, typical response time: <500ms

## Future Enhancements

- Async alert sending (Celery)
- Machine learning for hazard clustering
- Real-time hazard stream processing
- Driver history integration
- Customizable alert thresholds per driver
