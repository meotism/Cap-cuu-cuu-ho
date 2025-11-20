# Map Data System - OSM + S2 Integration

A comprehensive Python system for working with OpenStreetMap data using Google's S2 geometry library for efficient spatial indexing.

## Overview

This system provides:
- **OpenStreetMap Integration**: Fetch real-world map data using the Overpass API
- **S2 Cell Indexing**: Divide the map into hierarchical grid cells with unique IDs (based on Geohash algorithm)
- **Road Storage**: Store road metadata, segments, and turn restrictions organized by cells
- **Efficient Queries**: Fast spatial queries for roads, intersections, and navigation restrictions

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   MapManager                        │
│  (Coordinates all operations)                       │
└──────────┬──────────────┬──────────────┬───────────┘
           │              │              │
     ┌─────▼─────┐  ┌────▼─────┐  ┌─────▼──────┐
     │  S2Cell   │  │   OSM    │  │    Road    │
     │  Index    │  │  Fetcher │  │  Storage   │
     └───────────┘  └──────────┘  └────────────┘
```

## Installation

Required packages are already installed:
- `s2sphere` - Google S2 geometry library
- `overpy` - OpenStreetMap Overpass API client
- `requests` - HTTP requests
- `shapely` - Geometric operations
- `geojson` - GeoJSON export support

## Quick Start

```python
from map_manager import MapManager

# Initialize the manager
manager = MapManager(
    cell_level=15,  # ~1km cells
    storage_dir="./map_data"
)

# Load map data for an area (e.g., downtown San Francisco)
stats = manager.load_map_data_bbox(
    min_lat=37.785, min_lng=-122.410,
    max_lat=37.795, max_lng=-122.395,
    road_types=['primary', 'secondary', 'tertiary']
)

# Query roads at a specific location
result = manager.query_roads_at_location(37.7955, -122.3937)
print(f"Found {len(result['data']['roads'])} roads in this area")

# Save data for later use
manager.save_data("my_map_data.pkl")
```

## Module Documentation

### 1. S2CellIndex (`s2_cell_index.py`)

Handles spatial indexing using S2 geometry:

```python
from s2_cell_index import S2CellIndex

s2 = S2CellIndex(min_level=15, max_level=15)

# Get cell ID for a location
cell_id = s2.get_cell_id(37.7955, -122.3937)

# Get neighboring cells
neighbors = s2.get_neighbor_cells(cell_id)

# Get cells in a radius
cells = s2.get_cells_in_radius(37.7955, -122.3937, radius_meters=1000)

# Get cell bounds and center
bounds = s2.get_cell_bounds(cell_id)
center = s2.get_cell_center(cell_id)
```

**S2 Cell Levels**:
- Level 13: ~4 km × 4 km
- Level 15: ~1 km × 1 km (default)
- Level 17: ~250 m × 250 m

### 2. OSMDataFetcher (`osm_data_fetcher.py`)

Fetches map data from OpenStreetMap:

```python
from osm_data_fetcher import OSMDataFetcher

fetcher = OSMDataFetcher()

# Fetch roads in a bounding box
roads_data = fetcher.get_roads_in_bbox(
    min_lat, min_lng, max_lat, max_lng,
    road_types=['motorway', 'primary', 'secondary']
)

# Fetch roads around a point
roads_data = fetcher.get_roads_around_point(
    lat=37.7955, lng=-122.3937,
    radius_meters=500
)

# Get turn restrictions
restrictions = fetcher.get_turn_restrictions(min_lat, min_lng, max_lat, max_lng)

# Find intersections
intersections = fetcher.get_intersections(min_lat, min_lng, max_lat, max_lng)

# Parse road metadata
metadata = OSMDataFetcher.parse_road_metadata(road)
# Returns: name, highway_type, oneway, maxspeed, lanes, surface, etc.
```

### 3. RoadSegmentStore (`road_segment_store.py`)

Stores and queries road data organized by S2 cells:

```python
from road_segment_store import RoadSegmentStore

store = RoadSegmentStore(storage_dir="./map_data")

# Add data to cells
store.add_road_to_cell(cell_id, road_id, road_data)
store.add_turn_restriction(cell_id, restriction)
store.add_intersection(cell_id, intersection)

# Query data
roads = store.get_roads_in_cell(cell_id)
restrictions = store.get_turn_restrictions_in_cell(cell_id)

# Search operations
motorways = store.get_roads_by_type('motorway')
market_streets = store.get_roads_by_name('Market')

# Find specific roads
result = store.find_road_by_id(way_id)

# Statistics
stats = store.get_statistics()

# Persistence
store.save_to_disk("my_data.pkl")
store.load_from_disk("my_data.pkl")

# Export to GeoJSON
geojson = store.export_cell_to_geojson(cell_id, "output.geojson")
```

### 4. MapManager (`map_manager.py`)

High-level manager coordinating all operations:

```python
from map_manager import MapManager

manager = MapManager(cell_level=15, storage_dir="./map_data")

# Load map data
stats = manager.load_map_data_bbox(min_lat, min_lng, max_lat, max_lng)
stats = manager.load_map_data_around_point(lat, lng, radius_meters)

# Query operations
result = manager.query_roads_at_location(lat, lng)
area_data = manager.query_roads_in_area(min_lat, min_lng, max_lat, max_lng)

# Turn restriction queries
restrictions = manager.find_route_restrictions(from_road_id, to_road_id)

# Data management
manager.save_data("filename.pkl")
manager.load_data("filename.pkl")
manager.export_cell_geojson(cell_id, "output.geojson")

# Statistics
stats = manager.get_statistics()
```

## Example Usage

Run the comprehensive example:

```bash
python map_example.py
```

This demonstrates:
1. Loading map data from OpenStreetMap
2. S2 cell indexing and operations
3. Querying roads at specific locations
4. Searching for roads by name/type
5. Handling turn restrictions
6. Exporting to GeoJSON for visualization

## Data Structure

### Road Data
```python
{
    'id': 123456,  # OSM way ID
    'tags': {
        'highway': 'primary',
        'name': 'Market Street',
        'oneway': 'yes',
        'maxspeed': '35 mph',
        'lanes': '3'
    },
    'nodes': [node_id1, node_id2, ...],
    'node_coords': [(lat1, lng1), (lat2, lng2), ...],
    'metadata': {
        'name': 'Market Street',
        'highway_type': 'primary',
        'oneway': True,
        'maxspeed': '35 mph',
        'lanes': '3'
    }
}
```

### Turn Restriction Data
```python
{
    'id': 789012,  # OSM relation ID
    'tags': {
        'type': 'restriction',
        'restriction': 'no_left_turn'
    },
    'members': [
        {'type': 'way', 'ref': 123456, 'role': 'from'},
        {'type': 'node', 'ref': 234567, 'role': 'via'},
        {'type': 'way', 'ref': 345678, 'role': 'to'}
    ]
}
```

### Cell Data Structure
```python
{
    'roads': {road_id: road_data, ...},
    'turn_restrictions': [restriction1, restriction2, ...],
    'intersections': [intersection1, intersection2, ...],
    'metadata': {
        'road_count': 42,
        'last_updated': '2025-11-20T10:30:00'
    }
}
```

## Use Cases

### 1. Navigation Systems
- Store road network data efficiently
- Quick queries for nearby roads
- Handle turn restrictions for routing
- Identify intersections for navigation decisions

### 2. Map Visualization
- Export data to GeoJSON for web mapping
- Visualize roads by type (highways, streets, etc.)
- Display turn restrictions and intersections

### 3. Traffic Analysis
- Analyze road networks by area
- Query road types and capacities
- Identify bottlenecks and intersections

### 4. Location-Based Services
- Find nearby roads for address geocoding
- Determine which roads a vehicle can access
- Calculate routing constraints

## Performance Considerations

- **Cell Level**: Level 15 (~1km cells) provides good balance between granularity and performance
- **Rate Limiting**: OSM API requests are rate-limited (1 second between requests)
- **Caching**: Save loaded data to disk to avoid repeated API calls
- **Area Size**: Larger bounding boxes take longer to fetch; consider breaking into smaller chunks

## API Rate Limits

The Overpass API has usage limits:
- Wait at least 1 second between requests (enforced by `OSMDataFetcher`)
- Large queries may timeout (default: 60 seconds)
- Consider using a different endpoint for heavy usage

## Visualization

Export cells to GeoJSON and visualize at:
- [geojson.io](https://geojson.io/)
- [Mapbox Studio](https://studio.mapbox.com/)
- [QGIS](https://qgis.org/) (desktop GIS software)

## Future Enhancements

Potential additions:
- Database backend (PostgreSQL + PostGIS)
- Graph-based routing algorithms
- Real-time traffic integration
- Public transit data integration
- Elevation data support
- Multiple map layers (buildings, parks, etc.)

## License

This implementation uses:
- OpenStreetMap data (ODbL license)
- S2 Geometry (Apache 2.0 license)

## Troubleshooting

**Issue**: Slow data loading
- **Solution**: Reduce bounding box size or increase cell level

**Issue**: API timeout errors
- **Solution**: Reduce query area or increase timeout parameter

**Issue**: Missing roads in results
- **Solution**: Check road_types filter; remove to fetch all road types

**Issue**: Empty cells
- **Solution**: Verify coordinates are correct and area contains roads
