"""
LifeSaver Alert Engine - Demo and Test Examples

Shows how to use the alert engine with various scenarios.
"""

from core.alert_engine import lifesaver_alert_engine, LifeSaverAlertEngine
from core.models import Hazard
import json


def demo_basic_alert():
    """Demo 1: Basic alert engine usage"""
    print("\n" + "="*70)
    print("DEMO 1: Basic LifeSaver Alert Engine")
    print("="*70)
    
    # Example: Driver near hazards
    driver_phone = "+254712345678"
    driver_lat = 37.7749
    driver_lng = -122.4194
    
    print(f"\nDriver Location: ({driver_lat}, {driver_lng})")
    print(f"Phone: {driver_phone}")
    print(f"Search Radius: 300m\n")
    
    result = lifesaver_alert_engine(
        phone_number=driver_phone,
        latitude=driver_lat,
        longitude=driver_lng,
        radius_meters=300
    )
    
    print(f"Results:")
    print(f"  Hazards found: {result['nearby_hazards']}")
    print(f"  After dedup: {result['deduplicated']}")
    print(f"  Alerts sent: {result['alerts_sent']}")
    
    if result['hazards']:
        print(f"\nAlerting about:")
        for h in result['hazards']:
            print(f"  • {h['type']} (Severity {h['severity']})")
    
    if result['alerts']:
        print(f"\nAlert Details:")
        for alert in result['alerts']:
            print(f"  • {alert['hazard_type']}: {alert['message']}")


def demo_custom_radius():
    """Demo 2: Custom search radius"""
    print("\n" + "="*70)
    print("DEMO 2: Custom Search Radius")
    print("="*70)
    
    driver_phone = "+254712345678"
    driver_lat = 37.7749
    driver_lng = -122.4194
    
    for radius in [500, 1000, 2000]:
        print(f"\nSearching radius: {radius}m")
        
        result = lifesaver_alert_engine(
            phone_number=driver_phone,
            latitude=driver_lat,
            longitude=driver_lng,
            radius_meters=radius
        )
        
        print(f"  Found: {result['nearby_hazards']} hazards")
        print(f"  After dedup: {result['deduplicated']}")
        print(f"  Alerts: {result['alerts_sent']}")


def demo_severity_filtering():
    """Demo 3: Severity-based alert channels"""
    print("\n" + "="*70)
    print("DEMO 3: Severity-Based Alert Channels")
    print("="*70)
    
    print("\nAlert Channel Selection:")
    print("  Severity 1-2: No alert (below threshold)")
    print("  Severity 3: SMS alert")
    print("  Severity 4-5: VOICE alert (with SMS fallback)")
    
    driver_phone = "+254712345678"
    driver_lat = 37.7749
    driver_lng = -122.4194
    
    result = lifesaver_alert_engine(
        phone_number=driver_phone,
        latitude=driver_lat,
        longitude=driver_lng
    )
    
    print(f"\nHazards in range:")
    for hazard in result['hazards']:
        channel = "VOICE" if hazard['severity'] >= 4 else "SMS"
        print(f"  • {hazard['type']}: Severity {hazard['severity']} → {channel}")


def demo_deduplication():
    """Demo 4: Deduplication logic"""
    print("\n" + "="*70)
    print("DEMO 4: Hazard Deduplication")
    print("="*70)
    
    print("\nDeduplication Rules:")
    print("  1. Group hazards by type")
    print("  2. Same type within 50m = duplicate")
    print("  3. Keep highest severity + newest")
    
    driver_phone = "+254712345678"
    driver_lat = 37.7749
    driver_lng = -122.4194
    
    result = lifesaver_alert_engine(
        phone_number=driver_phone,
        latitude=driver_lat,
        longitude=driver_lng
    )
    
    print(f"\nExample result:")
    print(f"  Nearby hazards (before dedup): {result['nearby_hazards']}")
    print(f"  After deduplication: {result['deduplicated']}")
    print(f"  Reduction: {result['nearby_hazards'] - result['deduplicated']} duplicates removed")


def demo_step_by_step():
    """Demo 5: Step-by-step processing"""
    print("\n" + "="*70)
    print("DEMO 5: Step-by-Step Processing")
    print("="*70)
    
    driver_phone = "+254712345678"
    driver_lat = 37.7749
    driver_lng = -122.4194
    
    # Create engine
    engine = LifeSaverAlertEngine(
        phone_number=driver_phone,
        latitude=driver_lat,
        longitude=driver_lng,
        radius_meters=300
    )
    
    print(f"\nDriver: {driver_phone}")
    print(f"Location: ({driver_lat}, {driver_lng})")
    print(f"Radius: {engine.radius_meters}m\n")
    
    # Step 1
    print("Step 1: Find nearby hazards...")
    nearby = engine.find_nearby_hazards()
    print(f"  Found: {len(nearby)} hazards")
    for i, h in enumerate(nearby[:3], 1):
        dist = h.haversine_distance(driver_lat, driver_lng) if hasattr(h, 'haversine_distance') else "?"
        print(f"    {i}. {h.get_type_display()} (Severity {h.severity})")
    if len(nearby) > 3:
        print(f"    ... and {len(nearby) - 3} more")
    
    # Step 2
    print("\nStep 2: Deduplicate hazards...")
    dedup = engine.deduplicate_hazards()
    print(f"  After dedup: {len(dedup)} hazards")
    print(f"  Duplicates removed: {len(nearby) - len(dedup)}")
    
    # Step 3
    print("\nStep 3: Filter by severity (threshold >= 2)...")
    filtered = engine.filter_by_severity()
    print(f"  Passed filter: {len(filtered)} hazards")
    
    # Step 4
    print("\nStep 4: Send alerts...")
    for hazard in filtered[:3]:
        channel = "VOICE" if hazard.severity >= 4 else "SMS"
        print(f"  • {hazard.get_type_display()}: Send via {channel}")
    if len(filtered) > 3:
        print(f"  ... and {len(filtered) - 3} more")


def demo_json_output():
    """Demo 6: JSON output for API"""
    print("\n" + "="*70)
    print("DEMO 6: JSON Output (for API use)")
    print("="*70)
    
    driver_phone = "+254712345678"
    driver_lat = 37.7749
    driver_lng = -122.4194
    
    result = lifesaver_alert_engine(
        phone_number=driver_phone,
        latitude=driver_lat,
        longitude=driver_lng
    )
    
    print("\nJSON Response:")
    print(json.dumps(result, indent=2))


def run_all_demos():
    """Run all demo scenarios"""
    print("\n\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "LIFESAVER ALERT ENGINE - DEMO" + " "*24 + "║")
    print("╚" + "="*68 + "╝")
    
    demo_basic_alert()
    demo_custom_radius()
    demo_severity_filtering()
    demo_deduplication()
    demo_step_by_step()
    demo_json_output()
    
    print("\n\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nUsage in Django Views:")
    print("""
    from core.alert_engine import lifesaver_alert_engine
    
    result = lifesaver_alert_engine(
        phone_number=request.POST.get('phone'),
        latitude=float(request.POST.get('lat')),
        longitude=float(request.POST.get('lng')),
        radius_meters=300
    )
    
    return JsonResponse(result)
    """)


if __name__ == "__main__":
    run_all_demos()
