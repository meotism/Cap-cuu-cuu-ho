"""
Road Segment Storage Module

This module provides functionality to store road metadata, road segments,
and turn restrictions organized by S2 cells for efficient spatial queries.
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import defaultdict
import pickle


class RoadSegmentStore:
    """
    Stores road segments and metadata organized by S2 cell IDs.
    
    Each cell contains:
    - Road segments (sequences of coordinates)
    - Road metadata (name, type, speed limit, etc.)
    - Turn restrictions
    - Intersection information
    """
    
    def __init__(self, storage_dir: str = "./map_data"):
        """
        Initialize the Road Segment Store.
        
        Args:
            storage_dir: Directory to store map data files
        """
        self.storage_dir = storage_dir
        self.cell_data: Dict[str, Dict[str, Any]] = {}
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
    
    def add_road_to_cell(self, cell_id: str, road_id: int, road_data: Dict[str, Any]):
        """
        Add a road segment to a specific cell.
        
        Args:
            cell_id: S2 cell ID (token)
            road_id: OSM way ID
            road_data: Dictionary containing road information:
                - tags: Road tags from OSM
                - nodes: List of node IDs
                - node_coords: List of (lat, lng) tuples
                - metadata: Parsed metadata (optional)
        """
        if cell_id not in self.cell_data:
            self.cell_data[cell_id] = {
                'roads': {},
                'turn_restrictions': [],
                'intersections': [],
                'metadata': {
                    'road_count': 0,
                    'last_updated': None
                }
            }
        
        # Store road data
        self.cell_data[cell_id]['roads'][road_id] = road_data
        self.cell_data[cell_id]['metadata']['road_count'] = len(self.cell_data[cell_id]['roads'])
        
        # Update timestamp
        import datetime
        self.cell_data[cell_id]['metadata']['last_updated'] = datetime.datetime.now().isoformat()
    
    def add_turn_restriction(self, cell_id: str, restriction: Dict[str, Any]):
        """
        Add a turn restriction to a specific cell.
        
        Args:
            cell_id: S2 cell ID (token)
            restriction: Dictionary containing restriction information:
                - id: Relation ID
                - tags: Restriction tags (restriction type, etc.)
                - members: List of member ways and nodes involved
        """
        if cell_id not in self.cell_data:
            self.cell_data[cell_id] = {
                'roads': {},
                'turn_restrictions': [],
                'intersections': [],
                'metadata': {}
            }
        
        self.cell_data[cell_id]['turn_restrictions'].append(restriction)
    
    def add_intersection(self, cell_id: str, intersection: Dict[str, Any]):
        """
        Add an intersection to a specific cell.
        
        Args:
            cell_id: S2 cell ID (token)
            intersection: Dictionary containing intersection information:
                - node_id: OSM node ID
                - lat: Latitude
                - lng: Longitude
                - connected_roads: List of road IDs meeting at this point
        """
        if cell_id not in self.cell_data:
            self.cell_data[cell_id] = {
                'roads': {},
                'turn_restrictions': [],
                'intersections': [],
                'metadata': {}
            }
        
        self.cell_data[cell_id]['intersections'].append(intersection)
    
    def get_cell_data(self, cell_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve all data for a specific cell.
        
        Args:
            cell_id: S2 cell ID (token)
            
        Returns:
            Cell data dictionary or None if cell not found
        """
        return self.cell_data.get(cell_id)
    
    def get_roads_in_cell(self, cell_id: str) -> Dict[int, Dict[str, Any]]:
        """
        Get all roads in a specific cell.
        
        Args:
            cell_id: S2 cell ID (token)
            
        Returns:
            Dictionary mapping road IDs to road data
        """
        cell = self.cell_data.get(cell_id)
        if cell:
            return cell.get('roads', {})
        return {}
    
    def get_turn_restrictions_in_cell(self, cell_id: str) -> List[Dict[str, Any]]:
        """
        Get all turn restrictions in a specific cell.
        
        Args:
            cell_id: S2 cell ID (token)
            
        Returns:
            List of turn restriction dictionaries
        """
        cell = self.cell_data.get(cell_id)
        if cell:
            return cell.get('turn_restrictions', [])
        return []
    
    def get_intersections_in_cell(self, cell_id: str) -> List[Dict[str, Any]]:
        """
        Get all intersections in a specific cell.
        
        Args:
            cell_id: S2 cell ID (token)
            
        Returns:
            List of intersection dictionaries
        """
        cell = self.cell_data.get(cell_id)
        if cell:
            return cell.get('intersections', [])
        return []
    
    def find_road_by_id(self, road_id: int) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Find a road by its OSM way ID across all cells.
        
        Args:
            road_id: OSM way ID
            
        Returns:
            Tuple of (cell_id, road_data) or None if not found
        """
        for cell_id, cell_data in self.cell_data.items():
            if road_id in cell_data.get('roads', {}):
                return (cell_id, cell_data['roads'][road_id])
        return None
    
    def get_roads_by_type(self, highway_type: str, cell_ids: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find roads of a specific type (e.g., 'motorway', 'primary').
        
        Args:
            highway_type: Highway type from OSM tags
            cell_ids: Optional list of cell IDs to search within. If None, searches all cells.
            
        Returns:
            Dictionary mapping cell IDs to lists of matching roads
        """
        results = defaultdict(list)
        
        cells_to_search = cell_ids if cell_ids else self.cell_data.keys()
        
        for cell_id in cells_to_search:
            if cell_id in self.cell_data:
                for road_id, road_data in self.cell_data[cell_id]['roads'].items():
                    tags = road_data.get('tags', {})
                    if tags.get('highway') == highway_type:
                        results[cell_id].append({
                            'road_id': road_id,
                            'road_data': road_data
                        })
        
        return dict(results)
    
    def get_roads_by_name(self, name: str, cell_ids: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find roads by name.
        
        Args:
            name: Road name to search for (case-insensitive)
            cell_ids: Optional list of cell IDs to search within
            
        Returns:
            Dictionary mapping cell IDs to lists of matching roads
        """
        results = defaultdict(list)
        name_lower = name.lower()
        
        cells_to_search = cell_ids if cell_ids else self.cell_data.keys()
        
        for cell_id in cells_to_search:
            if cell_id in self.cell_data:
                for road_id, road_data in self.cell_data[cell_id]['roads'].items():
                    tags = road_data.get('tags', {})
                    road_name = tags.get('name', '').lower()
                    if name_lower in road_name:
                        results[cell_id].append({
                            'road_id': road_id,
                            'road_data': road_data
                        })
        
        return dict(results)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with statistics about stored data
        """
        total_roads = 0
        total_restrictions = 0
        total_intersections = 0
        
        for cell_data in self.cell_data.values():
            total_roads += len(cell_data.get('roads', {}))
            total_restrictions += len(cell_data.get('turn_restrictions', []))
            total_intersections += len(cell_data.get('intersections', []))
        
        return {
            'total_cells': len(self.cell_data),
            'total_roads': total_roads,
            'total_turn_restrictions': total_restrictions,
            'total_intersections': total_intersections,
            'avg_roads_per_cell': total_roads / len(self.cell_data) if self.cell_data else 0
        }
    
    def save_to_disk(self, filename: Optional[str] = None):
        """
        Save all cell data to disk.
        
        Args:
            filename: Optional filename. If None, uses default naming scheme.
        """
        if filename is None:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"road_segments_{timestamp}.pkl"
        
        filepath = os.path.join(self.storage_dir, filename)
        
        with open(filepath, 'wb') as f:
            pickle.dump(self.cell_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        print(f"Saved road segment data to {filepath}")
        
        # Also save a JSON summary for human readability
        json_filepath = filepath.replace('.pkl', '_summary.json')
        summary = {
            'statistics': self.get_statistics(),
            'cells': list(self.cell_data.keys())
        }
        
        with open(json_filepath, 'w') as f:
            json.dump(summary, f, indent=2)
    
    def load_from_disk(self, filename: str):
        """
        Load cell data from disk.
        
        Args:
            filename: Filename to load from (relative to storage_dir)
        """
        filepath = os.path.join(self.storage_dir, filename)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(filepath, 'rb') as f:
            self.cell_data = pickle.load(f)
        
        print(f"Loaded road segment data from {filepath}")
        print(f"Statistics: {self.get_statistics()}")
    
    def export_cell_to_geojson(self, cell_id: str, output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Export a cell's road data to GeoJSON format.
        
        Args:
            cell_id: S2 cell ID to export
            output_file: Optional file path to save GeoJSON
            
        Returns:
            GeoJSON FeatureCollection dictionary
        """
        cell_data = self.get_cell_data(cell_id)
        if not cell_data:
            return {'type': 'FeatureCollection', 'features': []}
        
        features = []
        
        # Add roads as LineString features
        for road_id, road_data in cell_data.get('roads', {}).items():
            coords = road_data.get('node_coords', [])
            if len(coords) < 2:
                continue
            
            # Convert to GeoJSON coordinate format [lng, lat]
            geojson_coords = [[lng, lat] for lat, lng in coords]
            
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'LineString',
                    'coordinates': geojson_coords
                },
                'properties': {
                    'road_id': road_id,
                    'cell_id': cell_id,
                    **road_data.get('tags', {})
                }
            }
            features.append(feature)
        
        # Add intersections as Point features
        for intersection in cell_data.get('intersections', []):
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [intersection['lng'], intersection['lat']]
                },
                'properties': {
                    'type': 'intersection',
                    'node_id': intersection['node_id'],
                    'connected_roads': intersection['connected_roads']
                }
            }
            features.append(feature)
        
        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        
        # Save to file if requested
        if output_file:
            filepath = os.path.join(self.storage_dir, output_file)
            with open(filepath, 'w') as f:
                json.dump(geojson, f, indent=2)
            print(f"Exported GeoJSON to {filepath}")
        
        return geojson
    
    def clear_cell(self, cell_id: str):
        """
        Clear all data for a specific cell.
        
        Args:
            cell_id: S2 cell ID to clear
        """
        if cell_id in self.cell_data:
            del self.cell_data[cell_id]
    
    def clear_all(self):
        """Clear all stored data."""
        self.cell_data = {}
