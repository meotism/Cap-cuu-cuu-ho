"""
Map Data Example - Demonstrates OSM + S2 Integration

This example shows how to use the map data system to:
1. Load map data from OpenStreetMap
2. Index it using S2 cells
3. Store and query road segments and turn restrictions
"""

from map_manager import MapManager


def example_load_city_area():
    """
    Example: Load map data for a city area (San Francisco downtown).
    """
    print("=" * 60)
    print("Example 1: Loading Map Data for San Francisco Downtown")
    print("=" * 60)
    
    # Initialize map manager
    manager = MapManager(
        cell_level=15,  # ~1km cells
        storage_dir="./map_data"
    )
    
    # San Francisco downtown coordinates
    # Roughly covers Market St, Financial District area
    min_lat, min_lng = 37.785, -122.410
    max_lat, max_lng = 37.795, -122.395
    
    # Load map data - filter for major roads only
    stats = manager.load_map_data_bbox(
        min_lat, min_lng, max_lat, max_lng,
        road_types=['motorway', 'trunk', 'primary', 'secondary', 'tertiary']
    )
    
    print(f"\n✓ Loaded and indexed map data successfully!")
    
    # Save the data
    manager.save_data("sf_downtown_map.pkl")
    print("✓ Saved map data to disk")
    
    return manager


def example_query_location(manager: MapManager):
    """
    Example: Query roads at a specific location.
    """
    print("\n" + "=" * 60)
    print("Example 2: Querying Roads at a Location")
    print("=" * 60)
    
    # Query a specific point (e.g., Ferry Building area)
    lat, lng = 37.7955, -122.3937
    
    result = manager.query_roads_at_location(lat, lng)
    
    print(f"\nQuerying location: ({lat}, {lng})")
    print(f"S2 Cell ID: {result['cell_id']}")
    print(f"Cell Center: {result['cell_center']}")
    
    if result['data']:
        roads = result['data'].get('roads', {})
        print(f"\nRoads in this cell: {len(roads)}")
        
        # Show first 5 roads
        for i, (road_id, road_data) in enumerate(list(roads.items())[:5]):
            metadata = road_data.get('metadata', {})
            print(f"  {i+1}. {metadata.get('name', 'Unnamed')} ({metadata.get('highway_type', 'unknown')})")
        
        intersections = result['data'].get('intersections', [])
        print(f"\nIntersections in this cell: {len(intersections)}")
        
        turn_restrictions = result['data'].get('turn_restrictions', [])
        print(f"Turn restrictions in this cell: {len(turn_restrictions)}")


def example_search_roads(manager: MapManager):
    """
    Example: Search for roads by name or type.
    """
    print("\n" + "=" * 60)
    print("Example 3: Searching for Roads")
    print("=" * 60)
    
    # Search for roads named "Market"
    print("\nSearching for roads containing 'Market'...")
    results = manager.road_store.get_roads_by_name("Market")
    
    total_found = sum(len(roads) for roads in results.values())
    print(f"Found {total_found} road segments across {len(results)} cells")
    
    for cell_id, roads in list(results.items())[:2]:  # Show first 2 cells
        print(f"\n  Cell {cell_id}:")
        for road in roads[:3]:  # Show first 3 roads
            metadata = road['road_data'].get('metadata', {})
            tags = road['road_data'].get('tags', {})
            print(f"    - {metadata.get('name')} (Type: {metadata.get('highway_type')})")
            if metadata.get('oneway'):
                print(f"      ONE-WAY")
    
    # Search for motorways
    print("\n\nSearching for motorways...")
    motorways = manager.road_store.get_roads_by_type('motorway')
    
    total_motorways = sum(len(roads) for roads in motorways.values())
    print(f"Found {total_motorways} motorway segments across {len(motorways)} cells")


def example_s2_cell_operations():
    """
    Example: Demonstrate S2 cell operations.
    """
    print("\n" + "=" * 60)
    print("Example 4: S2 Cell Operations")
    print("=" * 60)
    
    from s2_cell_index import S2CellIndex
    
    s2 = S2CellIndex(min_level=15, max_level=15)
    
    # Get cell for a location
    lat, lng = 37.7955, -122.3937
    cell_token = s2.get_cell_id(lat, lng)
    
    print(f"\nLocation: ({lat}, {lng})")
    print(f"Cell Token: {cell_token}")
    print(f"Cell Level: {s2.get_cell_level(cell_token)}")
    
    # Get cell bounds
    bounds = s2.get_cell_bounds(cell_token)
    print(f"Cell Bounds: {bounds}")
    
    # Get cell center
    center = s2.get_cell_center(cell_token)
    print(f"Cell Center: {center}")
    
    # Get neighboring cells
    neighbors = s2.get_neighbor_cells(cell_token)
    print(f"\nNeighboring cells: {len(neighbors)}")
    for i, neighbor in enumerate(neighbors[:4]):
        print(f"  {i+1}. {neighbor}")
    
    # Get cells in radius
    print(f"\nCells within 500m radius:")
    cells_in_radius = s2.get_cells_in_radius(lat, lng, 500)
    print(f"Total cells: {len(cells_in_radius)}")


def example_export_geojson(manager: MapManager):
    """
    Example: Export cell data to GeoJSON for visualization.
    """
    print("\n" + "=" * 60)
    print("Example 5: Exporting to GeoJSON")
    print("=" * 60)
    
    # Get a cell with data
    lat, lng = 37.7955, -122.3937
    cell_token = manager.s2_index.get_cell_id(lat, lng)
    
    # Export to GeoJSON
    geojson = manager.export_cell_geojson(cell_token, "sf_cell_export.geojson")
    
    print(f"\nExported cell {cell_token} to GeoJSON")
    print(f"Features in GeoJSON: {len(geojson['features'])}")
    print("\n✓ You can visualize this GeoJSON file at: https://geojson.io/")


def example_turn_restrictions(manager: MapManager):
    """
    Example: Query turn restrictions between roads.
    """
    print("\n" + "=" * 60)
    print("Example 6: Turn Restrictions")
    print("=" * 60)
    
    # Get statistics
    stats = manager.get_statistics()
    
    print(f"\nTotal turn restrictions in dataset: {stats['total_turn_restrictions']}")
    
    # If we have any restrictions, show an example
    if stats['total_turn_restrictions'] > 0:
        # Find a cell with turn restrictions
        for cell_token in manager.road_store.cell_data.keys():
            restrictions = manager.road_store.get_turn_restrictions_in_cell(cell_token)
            if restrictions:
                print(f"\nExample restriction from cell {cell_token}:")
                restriction = restrictions[0]
                print(f"  Restriction ID: {restriction['id']}")
                print(f"  Type: {restriction['tags'].get('restriction', 'unknown')}")
                print(f"  Members involved: {len(restriction['members'])}")
                
                for member in restriction['members']:
                    print(f"    - {member['role']}: {member['type']} {member['ref']}")
                break


def example_area_query(manager: MapManager):
    """
    Example: Query all roads in an area.
    """
    print("\n" + "=" * 60)
    print("Example 7: Area Query")
    print("=" * 60)
    
    # Query a small area
    min_lat, min_lng = 37.790, -122.405
    max_lat, max_lng = 37.792, -122.400
    
    print(f"\nQuerying area: ({min_lat}, {min_lng}) to ({max_lat}, {max_lng})")
    
    results = manager.query_roads_in_area(min_lat, min_lng, max_lat, max_lng)
    
    print(f"\nArea covered by {results['summary']['total_cells']} S2 cells")
    print(f"Total roads: {results['summary']['total_roads']}")
    print(f"Total intersections: {results['summary']['total_intersections']}")
    print(f"Total turn restrictions: {results['summary']['total_turn_restrictions']}")
    
    # Show roads from first cell
    if results['cells']:
        first_cell = list(results['cells'].keys())[0]
        cell_data = results['cells'][first_cell]
        print(f"\nSample roads from cell {first_cell}:")
        
        for i, (road_id, road_data) in enumerate(list(cell_data['roads'].items())[:3]):
            metadata = road_data.get('metadata', {})
            print(f"  {i+1}. {metadata.get('name', 'Unnamed')} ({metadata.get('highway_type')})")


def main():
    """
    Run all examples.
    """
    print("\n" + "=" * 60)
    print("MAP DATA SYSTEM - COMPLETE DEMONSTRATION")
    print("OpenStreetMap + Google S2 Integration")
    print("=" * 60)
    
    # Example 1: Load map data
    print("\n⚠ Note: This will fetch real data from OpenStreetMap.")
    print("The first load may take a minute or two depending on the area size.")
    
    import sys
    response = input("\nContinue with live OSM data fetch? (y/n): ")
    if response.lower() != 'y':
        print("\nDemo cancelled. You can modify the coordinates in the script")
        print("to fetch data for your area of interest.")
        return
    
    try:
        # Load data for SF downtown
        manager = example_load_city_area()
        
        # Run other examples
        example_query_location(manager)
        example_search_roads(manager)
        example_s2_cell_operations()
        example_export_geojson(manager)
        example_turn_restrictions(manager)
        example_area_query(manager)
        
        print("\n" + "=" * 60)
        print("✓ ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        print("\n📊 Final Statistics:")
        stats = manager.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\n💾 Map data has been saved to: ./map_data/sf_downtown_map.pkl")
        print("📍 GeoJSON export saved to: ./map_data/sf_cell_export.geojson")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        print("\nThis might be due to:")
        print("  1. Network connectivity issues")
        print("  2. Overpass API rate limiting")
        print("  3. Invalid coordinates")
        print("\nTry again in a few minutes or adjust the area size.")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
