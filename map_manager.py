"""
Map Manager Module

This module coordinates OSM data fetching, S2 cell indexing, and road storage
to provide a complete map data management system.
"""

from typing import List, Dict, Tuple, Optional, Any
from s2_cell_index import S2CellIndex
from osm_data_fetcher import OSMDataFetcher
from road_segment_store import RoadSegmentStore


class MapManager:
    """
    High-level manager for map data operations.
    
    Coordinates between:
    - S2 cell indexing for spatial organization
    - OSM data fetching for map content
    - Road segment storage for efficient queries
    """
    
    def __init__(self, 
                 cell_level: int = 15,
                 storage_dir: str = "./map_data",
                 osm_endpoint: str = "https://overpass-api.de/api/interpreter"):
        """
        Initialize the Map Manager.
        
        Args:
            cell_level: S2 cell level (15 = ~1km cells, 13 = ~4km cells)
            storage_dir: Directory for storing map data
            osm_endpoint: Overpass API endpoint
        """
        self.s2_index = S2CellIndex(min_level=cell_level, max_level=cell_level)
        self.osm_fetcher = OSMDataFetcher(endpoint=osm_endpoint)
        self.road_store = RoadSegmentStore(storage_dir=storage_dir)
        
        self.cell_level = cell_level
    
    def load_map_data_bbox(self, min_lat: float, min_lng: float,
                           max_lat: float, max_lng: float,
                           road_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Load and index map data for a bounding box area.
        
        Args:
            min_lat: Minimum latitude
            min_lng: Minimum longitude
            max_lat: Maximum latitude
            max_lng: Maximum longitude
            road_types: Optional list of highway types to filter
            
        Returns:
            Dictionary with statistics about loaded data
        """
        print(f"Fetching map data for bbox: ({min_lat}, {min_lng}) to ({max_lat}, {max_lng})")
        
        # Get S2 cells covering this area
        cell_tokens = self.s2_index.get_cells_in_bbox(min_lat, min_lng, max_lat, max_lng)
        print(f"Area covered by {len(cell_tokens)} S2 cells at level {self.cell_level}")
        
        # Fetch road data from OSM
        roads_data = self.osm_fetcher.get_roads_in_bbox(
            min_lat, min_lng, max_lat, max_lng, road_types
        )
        print(f"Fetched {len(roads_data['roads'])} roads from OpenStreetMap")
        
        # Fetch turn restrictions
        print("Fetching turn restrictions...")
        turn_restrictions = self.osm_fetcher.get_turn_restrictions(
            min_lat, min_lng, max_lat, max_lng
        )
        print(f"Fetched {len(turn_restrictions)} turn restrictions")
        
        # Fetch intersections
        print("Finding intersections...")
        intersections = self.osm_fetcher.get_intersections(
            min_lat, min_lng, max_lat, max_lng
        )
        print(f"Found {len(intersections)} intersections")
        
        # Index roads by S2 cells
        print("Indexing roads into S2 cells...")
        road_cell_mapping = self._map_roads_to_cells(roads_data['roads'])
        
        # Store roads in cells
        for cell_token, road_ids in road_cell_mapping.items():
            for road_id in road_ids:
                # Find the road data
                road = next((r for r in roads_data['roads'] if r['id'] == road_id), None)
                if road:
                    # Parse metadata
                    metadata = OSMDataFetcher.parse_road_metadata(road)
                    road['metadata'] = metadata
                    
                    # Add to store
                    self.road_store.add_road_to_cell(cell_token, road_id, road)
        
        # Index turn restrictions by cells
        print("Indexing turn restrictions...")
        for restriction in turn_restrictions:
            # Find which cell(s) this restriction belongs to
            cells = self._get_cells_for_restriction(restriction, roads_data)
            for cell_token in cells:
                self.road_store.add_turn_restriction(cell_token, restriction)
        
        # Index intersections by cells
        print("Indexing intersections...")
        for intersection in intersections:
            cell_token = self.s2_index.get_cell_id(
                intersection['lat'], intersection['lng']
            )
            self.road_store.add_intersection(cell_token, intersection)
        
        stats = self.road_store.get_statistics()
        print(f"\nIndexing complete!")
        print(f"Total cells with data: {stats['total_cells']}")
        print(f"Total roads indexed: {stats['total_roads']}")
        print(f"Total turn restrictions: {stats['total_turn_restrictions']}")
        print(f"Total intersections: {stats['total_intersections']}")
        
        return stats
    
    def load_map_data_around_point(self, lat: float, lng: float,
                                   radius_meters: float,
                                   road_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Load and index map data around a specific point.
        
        Args:
            lat: Center latitude
            lng: Center longitude
            radius_meters: Radius in meters
            road_types: Optional list of highway types to filter
            
        Returns:
            Dictionary with statistics about loaded data
        """
        print(f"Fetching map data around ({lat}, {lng}) with radius {radius_meters}m")
        
        # Get S2 cells covering this area
        cell_tokens = self.s2_index.get_cells_in_radius(lat, lng, radius_meters)
        print(f"Area covered by {len(cell_tokens)} S2 cells at level {self.cell_level}")
        
        # Fetch road data from OSM
        roads_data = self.osm_fetcher.get_roads_around_point(
            lat, lng, radius_meters, road_types
        )
        print(f"Fetched {len(roads_data['roads'])} roads from OpenStreetMap")
        
        # Convert radius query to approximate bbox for restrictions/intersections
        # Simple approximation: 1 degree ≈ 111km at equator
        lat_offset = (radius_meters / 111000)
        lng_offset = (radius_meters / (111000 * abs(lat / 90)))  # Rough longitude correction
        
        min_lat, max_lat = lat - lat_offset, lat + lat_offset
        min_lng, max_lng = lng - lng_offset, lng + lng_offset
        
        # Fetch turn restrictions
        print("Fetching turn restrictions...")
        turn_restrictions = self.osm_fetcher.get_turn_restrictions(
            min_lat, min_lng, max_lat, max_lng
        )
        print(f"Fetched {len(turn_restrictions)} turn restrictions")
        
        # Intersections are already computed during road fetch
        intersections = self.osm_fetcher.get_intersections(
            min_lat, min_lng, max_lat, max_lng
        )
        print(f"Found {len(intersections)} intersections")
        
        # Index and store data (same as bbox method)
        print("Indexing roads into S2 cells...")
        road_cell_mapping = self._map_roads_to_cells(roads_data['roads'])
        
        for cell_token, road_ids in road_cell_mapping.items():
            for road_id in road_ids:
                road = next((r for r in roads_data['roads'] if r['id'] == road_id), None)
                if road:
                    metadata = OSMDataFetcher.parse_road_metadata(road)
                    road['metadata'] = metadata
                    self.road_store.add_road_to_cell(cell_token, road_id, road)
        
        print("Indexing turn restrictions...")
        for restriction in turn_restrictions:
            cells = self._get_cells_for_restriction(restriction, roads_data)
            for cell_token in cells:
                self.road_store.add_turn_restriction(cell_token, restriction)
        
        print("Indexing intersections...")
        for intersection in intersections:
            cell_token = self.s2_index.get_cell_id(
                intersection['lat'], intersection['lng']
            )
            self.road_store.add_intersection(cell_token, intersection)
        
        stats = self.road_store.get_statistics()
        print(f"\nIndexing complete!")
        print(f"Total cells with data: {stats['total_cells']}")
        print(f"Total roads indexed: {stats['total_roads']}")
        
        return stats
    
    def query_roads_at_location(self, lat: float, lng: float) -> Dict[str, Any]:
        """
        Query roads at a specific location.
        
        Args:
            lat: Latitude
            lng: Longitude
            
        Returns:
            Dictionary with cell info and roads in that cell
        """
        cell_token = self.s2_index.get_cell_id(lat, lng)
        cell_data = self.road_store.get_cell_data(cell_token)
        
        return {
            'cell_id': cell_token,
            'location': {'lat': lat, 'lng': lng},
            'cell_center': self.s2_index.get_cell_center(cell_token),
            'cell_bounds': self.s2_index.get_cell_bounds(cell_token),
            'data': cell_data
        }
    
    def query_roads_in_area(self, min_lat: float, min_lng: float,
                           max_lat: float, max_lng: float) -> Dict[str, Any]:
        """
        Query all roads in a bounding box area.
        
        Args:
            min_lat: Minimum latitude
            min_lng: Minimum longitude
            max_lat: Maximum latitude
            max_lng: Maximum longitude
            
        Returns:
            Dictionary with all roads in the area organized by cell
        """
        cell_tokens = self.s2_index.get_cells_in_bbox(min_lat, min_lng, max_lat, max_lng)
        
        results = {
            'bbox': {
                'min_lat': min_lat, 'min_lng': min_lng,
                'max_lat': max_lat, 'max_lng': max_lng
            },
            'cells': {},
            'summary': {
                'total_cells': len(cell_tokens),
                'total_roads': 0,
                'total_intersections': 0,
                'total_turn_restrictions': 0
            }
        }
        
        for cell_token in cell_tokens:
            cell_data = self.road_store.get_cell_data(cell_token)
            if cell_data:
                results['cells'][cell_token] = cell_data
                results['summary']['total_roads'] += len(cell_data.get('roads', {}))
                results['summary']['total_intersections'] += len(cell_data.get('intersections', []))
                results['summary']['total_turn_restrictions'] += len(cell_data.get('turn_restrictions', []))
        
        return results
    
    def find_route_restrictions(self, from_road_id: int, to_road_id: int) -> List[Dict[str, Any]]:
        """
        Find turn restrictions that apply when moving from one road to another.
        
        Args:
            from_road_id: Starting road OSM way ID
            to_road_id: Destination road OSM way ID
            
        Returns:
            List of applicable turn restrictions
        """
        restrictions = []
        
        # Find cells containing these roads
        from_result = self.road_store.find_road_by_id(from_road_id)
        to_result = self.road_store.find_road_by_id(to_road_id)
        
        if not from_result or not to_result:
            return restrictions
        
        from_cell, _ = from_result
        to_cell, _ = to_result
        
        # Check cells and their neighbors for restrictions
        cells_to_check = {from_cell, to_cell}
        cells_to_check.update(self.s2_index.get_neighbor_cells(from_cell))
        cells_to_check.update(self.s2_index.get_neighbor_cells(to_cell))
        
        for cell_token in cells_to_check:
            cell_restrictions = self.road_store.get_turn_restrictions_in_cell(cell_token)
            
            for restriction in cell_restrictions:
                # Check if restriction involves these roads
                members = restriction.get('members', [])
                member_refs = [m['ref'] for m in members]
                
                if from_road_id in member_refs and to_road_id in member_refs:
                    restrictions.append(restriction)
        
        return restrictions
    
    def save_data(self, filename: Optional[str] = None):
        """
        Save all map data to disk.
        
        Args:
            filename: Optional filename for the save file
        """
        self.road_store.save_to_disk(filename)
    
    def load_data(self, filename: str):
        """
        Load map data from disk.
        
        Args:
            filename: Filename to load from
        """
        self.road_store.load_from_disk(filename)
    
    def export_cell_geojson(self, cell_token: str, output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Export a cell's data to GeoJSON format.
        
        Args:
            cell_token: S2 cell token
            output_file: Optional output filename
            
        Returns:
            GeoJSON dictionary
        """
        return self.road_store.export_cell_to_geojson(cell_token, output_file)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about stored map data.
        
        Returns:
            Statistics dictionary
        """
        return self.road_store.get_statistics()
    
    # Private helper methods
    
    def _map_roads_to_cells(self, roads: List[Dict[str, Any]]) -> Dict[str, List[int]]:
        """
        Map roads to S2 cells based on their coordinates.
        
        Args:
            roads: List of road dictionaries
            
        Returns:
            Dictionary mapping cell tokens to lists of road IDs
        """
        cell_mapping = {}
        
        for road in roads:
            road_id = road['id']
            node_coords = road.get('node_coords', [])
            
            # Get all cells this road passes through
            road_cells = set()
            for lat, lng in node_coords:
                cell_token = self.s2_index.get_cell_id(lat, lng)
                road_cells.add(cell_token)
            
            # Add road to each cell it passes through
            for cell_token in road_cells:
                if cell_token not in cell_mapping:
                    cell_mapping[cell_token] = []
                if road_id not in cell_mapping[cell_token]:
                    cell_mapping[cell_token].append(road_id)
        
        return cell_mapping
    
    def _get_cells_for_restriction(self, restriction: Dict[str, Any],
                                   roads_data: Dict[str, Any]) -> List[str]:
        """
        Determine which cells a turn restriction belongs to.
        
        Args:
            restriction: Turn restriction dictionary
            roads_data: Roads data from OSM fetch
            
        Returns:
            List of cell tokens
        """
        cells = set()
        
        # Get the via node/way from restriction members
        members = restriction.get('members', [])
        
        for member in members:
            if member['type'] == 'node' and member['role'] == 'via':
                # Find this node in the roads data
                node_id = member['ref']
                if node_id in roads_data.get('nodes', {}):
                    node = roads_data['nodes'][node_id]
                    cell_token = self.s2_index.get_cell_id(node['lat'], node['lng'])
                    cells.add(cell_token)
        
        # If no via node found, use the roads involved
        if not cells:
            for member in members:
                if member['type'] == 'way':
                    way_id = member['ref']
                    # Find this way in roads
                    road = next((r for r in roads_data['roads'] if r['id'] == way_id), None)
                    if road and road.get('node_coords'):
                        # Use midpoint of the road
                        coords = road['node_coords']
                        mid_idx = len(coords) // 2
                        lat, lng = coords[mid_idx]
                        cell_token = self.s2_index.get_cell_id(lat, lng)
                        cells.add(cell_token)
        
        return list(cells)
