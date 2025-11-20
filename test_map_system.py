"""
Quick test script to validate the map system works correctly.
Tests each component individually before running the full example.
"""

def test_s2_cell_index():
    """Test S2 cell indexing."""
    print("Testing S2 Cell Index...")
    from s2_cell_index import S2CellIndex
    
    s2 = S2CellIndex(min_level=15, max_level=15)
    
    # Test basic cell operations
    lat, lng = 37.7955, -122.3937
    cell_id = s2.get_cell_id(lat, lng)
    print(f"  ✓ Get cell ID: {cell_id}")
    
    # Test cell bounds
    bounds = s2.get_cell_bounds(cell_id)
    print(f"  ✓ Get cell bounds: {bounds}")
    
    # Test cell center
    center = s2.get_cell_center(cell_id)
    print(f"  ✓ Get cell center: {center}")
    
    # Test neighbor cells
    neighbors = s2.get_neighbor_cells(cell_id)
    print(f"  ✓ Get neighbors: {len(neighbors)} cells")
    
    # Test cells in radius (this was causing the error)
    try:
        cells = s2.get_cells_in_radius(lat, lng, 500)
        print(f"  ✓ Get cells in radius: {len(cells)} cells")
    except Exception as e:
        print(f"  ✗ Get cells in radius failed: {e}")
        raise
    
    # Test cells in bbox
    try:
        cells = s2.get_cells_in_bbox(37.79, -122.40, 37.80, -122.39)
        print(f"  ✓ Get cells in bbox: {len(cells)} cells")
    except Exception as e:
        print(f"  ✗ Get cells in bbox failed: {e}")
        raise
    
    print("  ✓ S2 Cell Index: ALL TESTS PASSED\n")
    return True


def test_osm_data_fetcher():
    """Test OSM data fetcher (without making real API calls)."""
    print("Testing OSM Data Fetcher...")
    from osm_data_fetcher import OSMDataFetcher
    
    fetcher = OSMDataFetcher()
    print(f"  ✓ OSMDataFetcher initialized")
    
    # Test metadata parsing
    test_road = {
        'tags': {
            'name': 'Test Street',
            'highway': 'primary',
            'oneway': 'yes',
            'maxspeed': '50',
            'lanes': '2'
        }
    }
    
    metadata = OSMDataFetcher.parse_road_metadata(test_road)
    assert metadata['name'] == 'Test Street'
    assert metadata['highway_type'] == 'primary'
    assert metadata['oneway'] == True
    print(f"  ✓ Road metadata parsing works")
    
    print("  ✓ OSM Data Fetcher: TESTS PASSED\n")
    return True


def test_road_segment_store():
    """Test road segment storage."""
    print("Testing Road Segment Store...")
    from road_segment_store import RoadSegmentStore
    import tempfile
    import os
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        store = RoadSegmentStore(storage_dir=temp_dir)
        print(f"  ✓ RoadSegmentStore initialized")
        
        # Add test data
        cell_id = "test_cell_123"
        road_data = {
            'tags': {'name': 'Test Road', 'highway': 'primary'},
            'nodes': [1, 2, 3],
            'node_coords': [(37.79, -122.40), (37.80, -122.39)]
        }
        
        store.add_road_to_cell(cell_id, 12345, road_data)
        print(f"  ✓ Added road to cell")
        
        # Retrieve data
        retrieved = store.get_roads_in_cell(cell_id)
        assert 12345 in retrieved
        print(f"  ✓ Retrieved road from cell")
        
        # Get statistics
        stats = store.get_statistics()
        assert stats['total_cells'] == 1
        assert stats['total_roads'] == 1
        print(f"  ✓ Statistics working: {stats}")
        
        print("  ✓ Road Segment Store: ALL TESTS PASSED\n")
        return True
        
    finally:
        # Cleanup
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def test_map_manager():
    """Test map manager initialization."""
    print("Testing Map Manager...")
    from map_manager import MapManager
    import tempfile
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        manager = MapManager(
            cell_level=15,
            storage_dir=temp_dir
        )
        print(f"  ✓ MapManager initialized")
        
        # Test query without data (should return None or empty)
        result = manager.query_roads_at_location(37.7955, -122.3937)
        print(f"  ✓ Query roads at location works (no data yet)")
        
        print("  ✓ Map Manager: INITIALIZATION TESTS PASSED\n")
        return True
        
    finally:
        import shutil
        import os
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def main():
    """Run all tests."""
    print("=" * 60)
    print("MAP SYSTEM VALIDATION TESTS")
    print("=" * 60)
    print()
    
    tests = [
        ("S2 Cell Index", test_s2_cell_index),
        ("OSM Data Fetcher", test_osm_data_fetcher),
        ("Road Segment Store", test_road_segment_store),
        ("Map Manager", test_map_manager),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"  ✗ {test_name} FAILED: {e}\n")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n✓ ALL VALIDATION TESTS PASSED!")
        print("\nThe map system is ready to use.")
        print("Run 'python map_example.py' to see the full demo.")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        print("Please review the errors above.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
