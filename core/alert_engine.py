"""
LifeSaver Alert Engine - Main Alert Service

Coordinates all alert logic:
1. Find hazards within radius
2. Deduplicate hazards
3. Prioritize by severity
4. Send voice/SMS alerts
5. Log all alerts
"""

from typing import List, Dict, Tuple
from core.models import Hazard, AlertLog
from core.utils import (
    haversine_distance,
    is_driver_near_hazard,
    make_voice_call,
    send_voice_alert_with_fallback,
    send_sms_alert_with_fatigue_check,
    has_recent_alert
)
from django.utils import timezone


class LifeSaverAlertEngine:
    """
    Main alert engine for SafeRoute.
    
    Finds nearby hazards and sends appropriate alerts to drivers.
    """
    
    # Configuration
    DEFAULT_RADIUS_METERS = 300
    SEVERITY_THRESHOLD = 2  # Only alert for severity >= 2
    
    def __init__(self, phone_number: str, latitude: float, longitude: float, radius_meters: int = None):
        """
        Initialize the alert engine.
        
        Args:
            phone_number: Driver's phone number
            latitude: Driver's current latitude
            longitude: Driver's current longitude
            radius_meters: Search radius (default: 300m)
        """
        self.phone_number = phone_number
        self.latitude = latitude
        self.longitude = longitude
        self.radius_meters = radius_meters or self.DEFAULT_RADIUS_METERS
        self.nearby_hazards = []
        self.deduplicated_hazards = []
        self.alerts_sent = []
    
    def find_nearby_hazards(self) -> List[Hazard]:
        """
        Find all hazards within the search radius.
        
        Returns:
            List of Hazard objects within radius, sorted by distance
        """
        all_hazards = Hazard.objects.all()
        nearby = []
        
        for hazard in all_hazards:
            distance = haversine_distance(
                self.latitude, self.longitude,
                hazard.latitude, hazard.longitude
            )
            
            # Include hazards within radius
            if distance <= self.radius_meters:
                nearby.append({
                    'hazard': hazard,
                    'distance': distance
                })
        
        # Sort by distance (closest first)
        nearby.sort(key=lambda x: x['distance'])
        
        # Extract hazard objects
        self.nearby_hazards = [h['hazard'] for h in nearby]
        
        return self.nearby_hazards
    
    def deduplicate_hazards(self) -> List[Hazard]:
        """
        Remove duplicate hazards using deduplication rules:
        
        1. Same type within 50 meters = duplicate
        2. Keep highest severity
        3. Keep most recent
        
        Returns:
            Deduplicated list of hazards
        """
        if not self.nearby_hazards:
            return []
        
        # Group by type
        hazards_by_type = {}
        for hazard in self.nearby_hazards:
            htype = hazard.type
            if htype not in hazards_by_type:
                hazards_by_type[htype] = []
            hazards_by_type[htype].append(hazard)
        
        deduplicated = []
        
        # Process each type group
        for htype, hazards in hazards_by_type.items():
            if len(hazards) == 1:
                # Single hazard of this type
                deduplicated.append(hazards[0])
            else:
                # Multiple hazards - apply deduplication
                # Group nearby hazards (within 50m)
                clusters = []
                used = set()
                
                for i, h1 in enumerate(hazards):
                    if i in used:
                        continue
                    
                    cluster = [h1]
                    used.add(i)
                    
                    for j, h2 in enumerate(hazards[i+1:], i+1):
                        if j in used:
                            continue
                        
                        dist = haversine_distance(
                            h1.latitude, h1.longitude,
                            h2.latitude, h2.longitude
                        )
                        
                        if dist <= 50:  # Within 50 meters
                            cluster.append(h2)
                            used.add(j)
                    
                    clusters.append(cluster)
                
                # Keep best from each cluster
                for cluster in clusters:
                    # Sort by severity (desc), then by date (desc)
                    best = sorted(
                        cluster,
                        key=lambda x: (-x.severity, -x.created_at.timestamp())
                    )[0]
                    deduplicated.append(best)
        
        self.deduplicated_hazards = deduplicated
        return deduplicated
    
    def filter_by_severity(self) -> List[Hazard]:
        """
        Filter hazards by minimum severity threshold.
        
        Returns:
            List of hazards meeting severity threshold
        """
        if not self.deduplicated_hazards:
            return []
        
        filtered = [
            h for h in self.deduplicated_hazards
            if h.severity >= self.SEVERITY_THRESHOLD
        ]
        
        return filtered
    
    def select_alert_channel(self, hazard: Hazard) -> str:
        """
        Select alert channel based on hazard severity.
        
        Rules:
        - Severity 4-5: VOICE (more urgent)
        - Severity 2-3: SMS (normal)
        
        Args:
            hazard: The hazard to alert about
            
        Returns:
            'VOICE' or 'SMS'
        """
        if hazard.severity >= 4:
            return 'VOICE'
        return 'SMS'
    
    def send_alert_for_hazard(self, hazard: Hazard) -> Tuple[bool, str]:
        """
        Send alert for a single hazard based on severity.
        
        Args:
            hazard: The Hazard to alert about
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        channel = self.select_alert_channel(hazard)
        
        if channel == 'VOICE':
            # High severity - use voice with SMS fallback
            voice_msg = f"Alert. {hazard.get_type_display()} ahead. Reduce speed immediately."
            sms_msg = f"🚨 {hazard.get_type_display().upper()}: Reduce speed immediately."
            
            success, voice_response, sms_response = send_voice_alert_with_fallback(
                self.phone_number,
                hazard,
                voice_message=voice_msg,
                sms_message=sms_msg
            )
            
            if sms_response:
                return success, f"VOICE FAILED, SMS FALLBACK: {sms_response}"
            return success, f"VOICE CALL: {voice_response}"
        
        else:
            # Normal severity - use SMS with fatigue check
            sms_msg = f"⚠️ {hazard.get_type_display()}: Ahead. Slow down."
            
            success, message = send_sms_alert_with_fatigue_check(
                self.phone_number,
                hazard,
                custom_message=sms_msg
            )
            
            return success, f"SMS: {message}"
    
    def process_alerts(self) -> Dict:
        """
        Main processing pipeline:
        1. Find nearby hazards
        2. Deduplicate
        3. Filter by severity
        4. Send alerts
        
        Returns:
            Dictionary with results:
            {
                'success': bool,
                'nearby_hazards': int,
                'deduplicated': int,
                'alerts_sent': int,
                'hazards': [...],
                'alerts': [...]
            }
        """
        # Step 1: Find nearby hazards
        self.find_nearby_hazards()
        nearby_count = len(self.nearby_hazards)
        
        # Step 2: Deduplicate
        self.deduplicate_hazards()
        dedup_count = len(self.deduplicated_hazards)
        
        # Step 3: Filter by severity
        hazards_to_alert = self.filter_by_severity()
        
        # Step 4: Send alerts
        for hazard in hazards_to_alert:
            success, message = self.send_alert_for_hazard(hazard)
            
            self.alerts_sent.append({
                'hazard_id': hazard.id,
                'hazard_type': hazard.get_type_display(),
                'severity': hazard.severity,
                'success': success,
                'message': message
            })
        
        return {
            'success': True,
            'nearby_hazards': nearby_count,
            'deduplicated': dedup_count,
            'alerts_sent': len(self.alerts_sent),
            'hazards': [
                {
                    'id': h.id,
                    'type': h.get_type_display(),
                    'severity': h.severity,
                    'lat': h.latitude,
                    'lng': h.longitude
                }
                for h in hazards_to_alert
            ],
            'alerts': self.alerts_sent
        }


def lifesaver_alert_engine(
    phone_number: str,
    latitude: float,
    longitude: float,
    radius_meters: int = 300
) -> Dict:
    """
    LifeSaver Alert Engine - Main entry point.
    
    Complete alert pipeline in one function suitable for demo/production use.
    
    Features:
    - Finds hazards within specified radius
    - Deduplicates based on type and proximity
    - Prioritizes by severity
    - Sends voice alerts for high severity (4-5)
    - Sends SMS alerts for normal severity (2-3)
    - Includes automatic SMS fallback for voice calls
    - Tracks all alert attempts
    
    Args:
        phone_number: Driver's phone number (e.g., "+254712345678")
        latitude: Driver's current latitude
        longitude: Driver's current longitude
        radius_meters: Search radius in meters (default: 300)
    
    Returns:
        Dictionary with results:
        {
            'success': bool - Whether processing succeeded
            'nearby_hazards': int - Hazards found in radius
            'deduplicated': int - After deduplication
            'alerts_sent': int - Number of alerts sent
            'hazards': [...] - List of hazards alerted
            'alerts': [...] - Details of each alert sent
        }
    
    Example Usage:
        result = lifesaver_alert_engine(
            phone_number="+254712345678",
            latitude=37.7749,
            longitude=-122.4194,
            radius_meters=300
        )
        
        if result['alerts_sent'] > 0:
            print(f"Alerts sent to {result['alerts_sent']} hazards")
            for alert in result['alerts']:
                print(alert['message'])
    """
    engine = LifeSaverAlertEngine(
        phone_number=phone_number,
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius_meters
    )
    
    return engine.process_alerts()
