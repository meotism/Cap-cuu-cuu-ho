"""
Simple Map System Demo - No API Calls Required

This demo shows the system capabilities without making real API calls.
For real data fetching, use map_example.py
"""

from s2_cell_index import S2CellIndex
from road_segment_store import RoadSegmentStore
from map_manager import MapManager
import tempfile


def demo_s2_cells():
    """Demonstrate S2 cell operations."""
    print("=" * 60)
    print("DEMO 1: S2 Cell Operations")
    print("=" * 60)
    
    s2 = S2CellIndex(min_level=15, max_level=15)
    
    # Example location: San Francisco Ferry Building
    lat, lng = 37.7955, -122.3937
    print(f"\nLocation: San Francisco Ferry Building")
    print(f"Coordinates: ({lat}, {lng})")
    
    # Get cell information
    cell_id = s2.get_cell_id(lat, lng)
    print(f"\nS2 Cell Token: {cell_id}")
    print(f"Cell Level: {s2.get_cell_level(cell_id)}")
    
    # Cell geometry
    center = s2.get_cell_center(cell_id)
    print(f"Cell Center: ({center[0]:.6f}, {center[1]:.6f})")
    
    bounds = s2.get_cell_bounds(cell_id)
    print(f"Cell Bounds:")
    print(f"  SW Corner: ({bounds[0][0]:.6f}, {bounds[0][1]:.6f})")
    print(f"  NE Corner: ({bounds[1][0]:.6f}, {bounds[1][1]:.6f})")
    
    # Cell dimensions (approximate)
    lat_diff = bounds[1][0] - bounds[0][0]
    lng_diff = bounds[1][1] - bounds[0][1]
    # Rough calculation: 1 degree ≈ 111 km
    height_km = lat_diff * 111
    width_km = lng_diff * 111 * 0.8  # Approximate for latitude
    print(f"\nApproximate Cell Size:")
    print(f"  Height: {height_km:.2f} km")
    print(f"  Width: {width_km:.2f} km")
    
    # Neighboring cells
    neighbors = s2.get_neighbor_cells(cell_id)
    print(f"\nNeighboring Cells: {len(neighbors)}")
    print(f"  Sample neighbors: {neighbors[:3]}")
    
    # Area coverage
    print(f"\nArea Coverage Examples:")
    
    # Small radius
    cells_500m = s2.get_cells_in_radius(lat, lng, 500)
    print(f"  500m radius: {len(cells_500m)} cells")
    
    # Medium radius
    cells_1km = s2.get_cells_in_radius(lat, lng, 1000)
    print(f"  1km radius: {len(cells_1km)} cells")
    
    # Bounding box
    cells_bbox = s2.get_cells_in_bbox(37.79, -122.40, 37.80, -122.39)
    print(f"  Small bbox: {len(cells_bbox)} cells")
    
    # Hierarchical cells
    print(f"\nCell Hierarchy:")
    parent_13 = s2.get_parent_cell(cell_id, 13)
    print(f"  Parent (Level 13, ~4km): {parent_13}")
    
    parent_10 = s2.get_parent_cell(cell_id, 10)
    print(f"  Grandparent (Level 10, ~30km): {parent_10}")
    
    print("\n✓ S2 Cell operations demonstrated\n")


def demo_road_storage():
    """Demonstrate road storage and queries."""
    print("=" * 60)
    print("DEMO 2: Road Storage and Queries")
    print("=" * 60)
    
    temp_dir = tempfile.mkdtemp()
    store = RoadSegmentStore(storage_dir=temp_dir)
    s2 = S2CellIndex(min_level=15, max_level=15)
    
    # Create sample road data
    print("\nAdding sample road data...")
    
    # Market Street segment
    cell_1 = s2.get_cell_id(37.7905, -122.4000)
    market_st = {
        'tags': {
            'name': 'Market Street',
            'highway': 'primary',
            'oneway': 'yes',
            'maxspeed': '35 mph',
            'lanes': '3',
            'surface': 'asphalt'
        },
        'nodes': [1001, 1002, 1003, 1004],
        'node_coords': [
            (37.7900, -122.4010),
            (37.7905, -122.4000),
            (37.7910, -122.3990),
            (37.7915, -122.3980)
        ],
        'metadata': {
            'name': 'Market Street',
            'highway_type': 'primary',
            'oneway': True,
            'maxspeed': '35 mph',
            'lanes': '3'
        }
    }
    store.add_road_to_cell(cell_1, 101, market_st)
    
    # Mission Street segment
    cell_2 = s2.get_cell_id(37.7895, -122.3995)
    mission_st = {
        'tags': {
            'name': 'Mission Street',
            'highway': 'secondary',
            'oneway': 'no',
            'maxspeed': '25 mph',
            'lanes': '2'
        },
        'nodes': [2001, 2002, 2003],
        'node_coords': [
            (37.7890, -122.4000),
            (37.7895, -122.3995),
            (37.7900, -122.3990)
        ],
        'metadata': {
            'name': 'Mission Street',
            'highway_type': 'secondary',
            'oneway': False,
            'maxspeed': '25 mph',
            'lanes': '2'
        }
    }
    store.add_road_to_cell(cell_2, 102, mission_st)
    
    # Highway 101 segment
    cell_3 = s2.get_cell_id(37.7850, -122.4050)
    hwy_101 = {
        'tags': {
            'name': 'US Highway 101',
            'highway': 'motorway',
            'oneway': 'yes',
            'maxspeed': '65 mph',
            'lanes': '4',
            'ref': 'US 101'
        },
        'nodes': [3001, 3002, 3003, 3004, 3005],
        'node_coords': [
            (37.7840, -122.4060),
            (37.7850, -122.4050),
            (37.7860, -122.4040),
            (37.7870, -122.4030),
            (37.7880, -122.4020)
        ],
        'metadata': {
            'name': 'US Highway 101',
            'highway_type': 'motorway',
            'oneway': True,
            'maxspeed': '65 mph',
            'lanes': '4',
            'ref': 'US 101'
        }
    }
    store.add_road_to_cell(cell_3, 103, hwy_101)
    
    # Add some intersections
    intersection_1 = {
        'node_id': 9001,
        'lat': 37.7905,
        'lng': -122.4000,
        'connected_roads': [101, 102],
        'tags': {'traffic_signals': 'yes'}
    }
    store.add_intersection(cell_1, intersection_1)
    
    # Add a turn restriction
    restriction = {
        'id': 5001,
        'tags': {
            'type': 'restriction',
            'restriction': 'no_left_turn'
        },
        'members': [
            {'type': 'way', 'ref': 101, 'role': 'from'},
            {'type': 'node', 'ref': 9001, 'role': 'via'},
            {'type': 'way', 'ref': 102, 'role': 'to'}
        ]
    }
    store.add_turn_restriction(cell_1, restriction)
    
    print("✓ Added 3 roads, 1 intersection, 1 turn restriction")
    
    # Query operations
    print("\n--- Query Operations ---")
    
    # Statistics
    stats = store.get_statistics()
    print(f"\nStorage Statistics:")
    print(f"  Total Cells: {stats['total_cells']}")
    print(f"  Total Roads: {stats['total_roads']}")
    print(f"  Total Intersections: {stats['total_intersections']}")
    print(f"  Total Turn Restrictions: {stats['total_turn_restrictions']}")
    print(f"  Avg Roads per Cell: {stats['avg_roads_per_cell']:.2f}")
    
    # Search by name
    print(f"\nSearch Results for 'Street':")
    results = store.get_roads_by_name('Street')
    for cell_id, roads in results.items():
        for road in roads:
            name = road['road_data']['metadata']['name']
            hwy_type = road['road_data']['metadata']['highway_type']
            print(f"  - {name} ({hwy_type})")
    
    # Search by type
    print(f"\nMotorways:")
    motorways = store.get_roads_by_type('motorway')
    for cell_id, roads in motorways.items():
        for road in roads:
            name = road['road_data']['metadata']['name']
            ref = road['road_data']['tags'].get('ref', 'N/A')
            print(f"  - {name} [Ref: {ref}]")
    
    # Get roads in a cell
    print(f"\nRoads in Cell {cell_1}:")
    cell_roads = store.get_roads_in_cell(cell_1)
    for road_id, road_data in cell_roads.items():
        metadata = road_data['metadata']
        print(f"  Road ID {road_id}: {metadata['name']}")
        print(f"    Type: {metadata['highway_type']}")
        print(f"    One-way: {metadata['oneway']}")
        print(f"    Speed: {metadata['maxspeed']}")
        print(f"    Segments: {len(road_data['node_coords'])} points")
    
    # Turn restrictions
    print(f"\nTurn Restrictions:")
    restrictions = store.get_turn_restrictions_in_cell(cell_1)
    for restr in restrictions:
        restr_type = restr['tags']['restriction']
        print(f"  {restr_type.replace('_', ' ').title()}")
        print(f"    From: Road {restr['members'][0]['ref']}")
        print(f"    Via: Node {restr['members'][1]['ref']}")
        print(f"    To: Road {restr['members'][2]['ref']}")
    
    print("\n✓ Storage and query operations demonstrated\n")
    
    # Cleanup
    import shutil
    import os
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


def demo_practical_usage():
    """Show practical usage scenarios."""
    print("=" * 60)
    print("DEMO 3: Practical Usage Scenarios")
    print("=" * 60)
    
    s2 = S2CellIndex(min_level=15, max_level=15)
    
    print("\nScenario 1: Route Planning")
    print("-" * 40)
    
    start = (37.7749, -122.4194)  # San Francisco City Hall
    end = (37.8044, -122.2711)    # Oakland Jack London Square
    
    print(f"Start: {start}")
    print(f"End: {end}")
    
    start_cell = s2.get_cell_id(start[0], start[1])
    end_cell = s2.get_cell_id(end[0], end[1])
    
    print(f"\nStart Cell: {start_cell}")
    print(f"End Cell: {end_cell}")
    
    # Calculate cells between points
    import math
    lat_diff = end[0] - start[0]
    lng_diff = end[1] - start[1]
    distance = math.sqrt(lat_diff**2 + lng_diff**2) * 111  # Rough km
    
    print(f"Approximate Distance: {distance:.2f} km")
    print(f"You would query roads in cells along this route")
    
    print("\nScenario 2: Nearby Roads")
    print("-" * 40)
    
    location = (37.7955, -122.3937)  # Ferry Building
    print(f"Location: Ferry Building {location}")
    
    # Find cells within walking distance (500m)
    nearby_cells = s2.get_cells_in_radius(location[0], location[1], 500)
    print(f"\nCells within 500m walking distance: {len(nearby_cells)}")
    print(f"Query these cells to find nearby roads and POIs")
    
    print("\nScenario 3: Area Analysis")
    print("-" * 40)
    
    # Downtown area
    bbox = (37.785, -122.410, 37.795, -122.395)
    print(f"Analyzing downtown area:")
    print(f"  SW: ({bbox[0]}, {bbox[1]})")
    print(f"  NE: ({bbox[2]}, {bbox[3]})")
    
    area_cells = s2.get_cells_in_bbox(*bbox)
    print(f"\nCells in area: {len(area_cells)}")
    print(f"Each cell contains:")
    print(f"  - Road segments")
    print(f"  - Intersections")
    print(f"  - Turn restrictions")
    print(f"  - Road metadata (names, types, speeds, etc.)")
    
    print("\n✓ Practical scenarios demonstrated\n")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("MAP SYSTEM - DEMONSTRATION (No API Calls)")
    print("OpenStreetMap + Google S2 Integration")
    print("=" * 60)
    print()
    
    try:
        demo_s2_cells()
        demo_road_storage()
        demo_practical_usage()
        
        print("=" * 60)
        print("✓ ALL DEMONSTRATIONS COMPLETED!")
        print("=" * 60)
        
        print("\n📚 Next Steps:")
        print("  1. Run 'python test_map_system.py' to validate all components")
        print("  2. Run 'python map_example.py' to fetch real OSM data")
        print("  3. Check MAP_README.md for complete documentation")
        
        print("\n💡 Key Takeaways:")
        print("  • S2 cells efficiently divide the map into grid cells")
        print("  • Each cell has a unique ID (token)")
        print("  • Roads are stored with their metadata and geometry")
        print("  • Turn restrictions help with navigation")
        print("  • Fast spatial queries by cell ID")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
