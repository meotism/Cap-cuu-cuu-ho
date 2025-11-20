"""
Quick Test: Create a single SOS post to test notifications
"""

import requests
import json

BASE_URL = "http://localhost:5000"

# Sample SOS post
test_post = {
    "user_name": "Test User",
    "user_phone": "+84 900 000 000",
    "title": "🔔 TEST NOTIFICATION - Car Accident",
    "description": "This is a test notification to demonstrate the real-time WebSocket notification system. All connected browsers should receive this alert!",
    "latitude": 21.0285,
    "longitude": 105.8542,
    "address": "Test Location, Hanoi",
    "priority": "critical"
}

print("=" * 70)
print("🔔 SENDING TEST NOTIFICATION")
print("=" * 70)
print()
print(f"📱 Title: {test_post['title']}")
print(f"📍 Location: {test_post['address']}")
print(f"⚠️  Priority: {test_post['priority'].upper()}")
print()
print("Sending...")

try:
    response = requests.post(
        f"{BASE_URL}/api/sos/create",
        json=test_post,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print()
            print("=" * 70)
            print("✅ SUCCESS!")
            print("=" * 70)
            print(f"Post ID: #{result['post_id']}")
            print()
            print("📢 Notification sent to all connected browsers!")
            print("   Check your browser - you should see:")
            print("   1. Slide-in notification (top-right)")
            print("   2. Post appears in sidebar")
            print("   3. Marker on map")
            print("   4. Beep sound")
            print()
        else:
            print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
    else:
        print(f"\n❌ HTTP Error: {response.status_code}")
        
except Exception as e:
    print(f"\n❌ Connection Error: {e}")
    print("   Make sure server is running: python map_server.py")

print("=" * 70)
