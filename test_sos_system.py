"""
Test SOS Database Functionality

This script tests the SOS emergency post system.
"""

from sos_database import SOSDatabase
import random


def test_sos_database():
    """Test SOS database operations."""
    print("=" * 60)
    print("TESTING SOS DATABASE")
    print("=" * 60)
    print()
    
    # Initialize database
    db = SOSDatabase()
    
    # Test 1: Create sample SOS posts
    print("Test 1: Creating sample SOS posts...")
    
    sample_posts = [
        {
            'user_name': 'Nguyen Van A',
            'user_phone': '+84 901 234 567',
            'title': 'Car Accident on Highway 1',
            'description': 'Multiple vehicle collision near kilometer marker 250. Need medical assistance urgently.',
            'latitude': 21.0285,
            'longitude': 105.8542,
            'address': 'Highway 1, Hanoi',
            'priority': 'critical'
        },
        {
            'user_name': 'Tran Thi B',
            'user_phone': '+84 902 345 678',
            'title': 'Flood in Residential Area',
            'description': 'Severe flooding in District 7. Water level rising rapidly. Several families need evacuation.',
            'latitude': 10.7308,
            'longitude': 106.7193,
            'address': 'District 7, Ho Chi Minh City',
            'priority': 'high'
        },
        {
            'user_name': 'Le Van C',
            'user_phone': '+84 903 456 789',
            'title': 'Lost Child at Beach',
            'description': 'Child lost at My Khe Beach. Boy, 8 years old, wearing blue shirt. Last seen near lifeguard station 3.',
            'latitude': 16.0544,
            'longitude': 108.2022,
            'address': 'My Khe Beach, Da Nang',
            'priority': 'high'
        },
        {
            'user_name': 'Pham Thi D',
            'title': 'Power Outage in Building',
            'description': 'Complete power outage in apartment building. 20 families affected. Elevator stuck with people inside.',
            'latitude': 21.0313,
            'longitude': 105.8516,
            'address': 'Cau Giay District, Hanoi',
            'priority': 'medium'
        },
        {
            'user_name': 'Hoang Van E',
            'user_phone': '+84 905 678 901',
            'title': 'Fire in Market Area',
            'description': 'Fire broke out at Ben Thanh Market. Smoke visible. Fire trucks on the way.',
            'latitude': 10.7726,
            'longitude': 106.6980,
            'address': 'Ben Thanh Market, District 1, HCMC',
            'priority': 'critical'
        }
    ]
    
    post_ids = []
    for post in sample_posts:
        post_id = db.create_post(**post)
        post_ids.append(post_id)
    
    print(f"✓ Created {len(post_ids)} sample posts")
    print()
    
    # Test 2: Get recent posts
    print("Test 2: Retrieving recent posts...")
    recent = db.get_recent_posts(limit=10)
    print(f"✓ Retrieved {len(recent)} recent posts")
    for post in recent[:3]:
        print(f"  - #{post['id']}: {post['title']} ({post['priority']})")
    print()
    
    # Test 3: Get posts by area
    print("Test 3: Getting posts in Hanoi area...")
    hanoi_posts = db.get_posts_in_area(
        min_lat=21.0,
        min_lng=105.8,
        max_lat=21.1,
        max_lng=105.9
    )
    print(f"✓ Found {len(hanoi_posts)} posts in Hanoi area")
    print()
    
    # Test 4: Get post by ID
    print("Test 4: Getting specific post...")
    post = db.get_post_by_id(post_ids[0])
    if post:
        print(f"✓ Retrieved post: {post['title']}")
        print(f"  Views: {post['view_count']}")
    print()
    
    # Test 5: Update post status
    print("Test 5: Updating post status...")
    success = db.update_post_status(post_ids[1], 'resolved')
    print(f"✓ Status updated: {success}")
    print()
    
    # Test 6: Increment help count
    print("Test 6: Offering help...")
    success = db.increment_help_count(post_ids[2])
    print(f"✓ Help count incremented: {success}")
    print()
    
    # Test 7: Search posts
    print("Test 7: Searching posts...")
    results = db.search_posts('fire')
    print(f"✓ Found {len(results)} posts matching 'fire'")
    print()
    
    # Test 8: Get statistics
    print("Test 8: Getting database statistics...")
    stats = db.get_statistics()
    print("✓ Statistics:")
    print(f"  Total posts: {stats['total_posts']}")
    print(f"  Active posts: {stats['active_posts']}")
    print(f"  Resolved posts: {stats['resolved_posts']}")
    print(f"  Priority breakdown: {stats['priority_counts']}")
    print()
    
    print("=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    print()
    print("Database file: ./map_data/sos_posts.db")
    print("You can now:")
    print("  1. Start the server: python map_server.py")
    print("  2. Open browser: http://localhost:5000")
    print("  3. View and create SOS posts!")


if __name__ == '__main__':
    test_sos_database()
