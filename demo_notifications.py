"""
Demo: Test WebSocket Notification System

This script simulates creating SOS posts to test the real-time notification system.
Open multiple browser windows at http://localhost:5000 to see notifications in real-time!
"""

import requests
import time
import random
from datetime import datetime

# Server URL
BASE_URL = "http://localhost:5000"

# Sample SOS posts for demo
DEMO_POSTS = [
    {
        "user_name": "Nguyen Van A",
        "user_phone": "+84 901 234 567",
        "title": "🚗 Car Accident on Highway 1",
        "description": "Multiple vehicle collision near kilometer marker 250. Need medical assistance urgently. Two people injured.",
        "latitude": 21.0285,
        "longitude": 105.8542,
        "address": "Highway 1, Hanoi",
        "priority": "critical"
    },
    {
        "user_name": "Tran Thi B",
        "user_phone": "+84 902 345 678",
        "title": "🌊 Flood in Residential Area",
        "description": "Severe flooding in District 7. Water level rising rapidly. Several families need evacuation assistance.",
        "latitude": 10.7308,
        "longitude": 106.7193,
        "address": "District 7, Ho Chi Minh City",
        "priority": "high"
    },
    {
        "user_name": "Le Van C",
        "user_phone": "+84 903 456 789",
        "title": "👶 Lost Child at Beach",
        "description": "Child lost at My Khe Beach. Boy, 8 years old, wearing blue shirt and red shorts. Last seen near lifeguard station 3.",
        "latitude": 16.0544,
        "longitude": 108.2022,
        "address": "My Khe Beach, Da Nang",
        "priority": "high"
    },
    {
        "user_name": "Pham Thi D",
        "user_phone": "+84 904 567 890",
        "title": "⚡ Power Outage in Building",
        "description": "Complete power outage in apartment building. 20 families affected. Elevator stuck with people inside on floor 12.",
        "latitude": 21.0313,
        "longitude": 105.8516,
        "address": "Cau Giay District, Hanoi",
        "priority": "medium"
    },
    {
        "user_name": "Hoang Van E",
        "user_phone": "+84 905 678 901",
        "title": "🔥 Fire in Market Area",
        "description": "Fire broke out at Ben Thanh Market. Smoke visible from multiple blocks. Fire trucks on the way.",
        "latitude": 10.7726,
        "longitude": 106.6980,
        "address": "Ben Thanh Market, District 1, HCMC",
        "priority": "critical"
    },
    {
        "user_name": "Do Thi F",
        "user_phone": "+84 906 789 012",
        "title": "🏥 Medical Emergency at School",
        "description": "Student collapsed during PE class. School nurse providing first aid. Need ambulance immediately.",
        "latitude": 16.0678,
        "longitude": 108.2208,
        "address": "Le Loi School, Da Nang",
        "priority": "critical"
    },
    {
        "user_name": "Bui Van G",
        "user_phone": "+84 907 890 123",
        "title": "🌳 Tree Fallen on Road",
        "description": "Large tree fell across main road after storm. Traffic completely blocked. No injuries reported.",
        "latitude": 10.8231,
        "longitude": 106.6297,
        "address": "District 3, Ho Chi Minh City",
        "priority": "medium"
    }
]

def create_sos_post(post_data):
    """Create a new SOS post."""
    try:
        response = requests.post(
            f"{BASE_URL}/api/sos/create",
            json=post_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Created SOS Post #{result['post_id']}: {post_data['title']}")
                print(f"   Priority: {post_data['priority'].upper()}")
                print(f"   Location: {post_data['address']}")
                print(f"   📢 Notification sent to all connected browsers!")
                return True
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print("   Make sure the server is running at http://localhost:5000")
        return False

def demo_continuous_mode():
    """Continuously create SOS posts with random delays."""
    print("=" * 70)
    print("🆘 SOS NOTIFICATION DEMO - CONTINUOUS MODE")
    print("=" * 70)
    print()
    print("📱 Open multiple browser windows at http://localhost:5000")
    print("   to see real-time notifications across all windows!")
    print()
    print("⏱️  Creating SOS posts every 10-15 seconds...")
    print("   Press Ctrl+C to stop")
    print()
    print("=" * 70)
    print()
    
    post_index = 0
    
    try:
        while True:
            post = DEMO_POSTS[post_index % len(DEMO_POSTS)]
            
            # Add timestamp to make each post unique
            post_copy = post.copy()
            post_copy['description'] += f" [Posted at {datetime.now().strftime('%H:%M:%S')}]"
            
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}]")
            create_sos_post(post_copy)
            
            post_index += 1
            
            # Random delay between 10-15 seconds
            delay = random.randint(10, 15)
            print(f"⏳ Next post in {delay} seconds...\n")
            time.sleep(delay)
            
    except KeyboardInterrupt:
        print("\n\n✋ Demo stopped by user")
        print("=" * 70)

def demo_single_mode():
    """Create posts one by one with user confirmation."""
    print("=" * 70)
    print("🆘 SOS NOTIFICATION DEMO - SINGLE MODE")
    print("=" * 70)
    print()
    print("📱 Open multiple browser windows at http://localhost:5000")
    print("   to see real-time notifications!")
    print()
    print("=" * 70)
    print()
    
    for i, post in enumerate(DEMO_POSTS, 1):
        print(f"\n{'='*70}")
        print(f"Post {i}/{len(DEMO_POSTS)}")
        print(f"{'='*70}")
        
        input(f"\nPress ENTER to create: {post['title']}")
        
        create_sos_post(post)
        
        print("\n✅ Check your browser windows for the notification!")
        time.sleep(2)
    
    print("\n\n" + "="*70)
    print("✅ Demo completed! All posts created.")
    print("="*70)

def main():
    """Main demo function."""
    print("\n")
    print("╔" + "═"*68 + "╗")
    print("║" + " "*15 + "🆘 SOS NOTIFICATION SYSTEM DEMO" + " "*22 + "║")
    print("╚" + "═"*68 + "╝")
    print()
    
    # Check server connection
    print("🔍 Checking server connection...")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running!")
            print(f"   {BASE_URL}")
        else:
            print("❌ Server not responding properly")
            return
    except Exception as e:
        print("❌ Cannot connect to server!")
        print("   Please start the server first:")
        print("   > python map_server.py")
        return
    
    print()
    print("Select demo mode:")
    print("  1. Continuous Mode (auto-post every 10-15 seconds)")
    print("  2. Single Mode (press ENTER for each post)")
    print()
    
    choice = input("Enter your choice (1 or 2): ").strip()
    
    print()
    
    if choice == "1":
        demo_continuous_mode()
    elif choice == "2":
        demo_single_mode()
    else:
        print("❌ Invalid choice. Please run again and select 1 or 2.")

if __name__ == '__main__':
    main()
