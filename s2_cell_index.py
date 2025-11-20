"""
S2 Cell Indexing Module

This module provides functionality to divide the map into grid cells using
Google's S2 geometry library and assign unique IDs to each cell based on
the Geohash algorithm.
"""

from s2sphere import Cell, CellId, LatLng, RegionCoverer, Cap, LatLngRect, Angle
from typing import List, Tuple, Set
import math


class S2CellIndex:
    """
    S2 Cell indexing system for efficient spatial queries.
    
    The S2 library divides the Earth's surface into hierarchical cells.
    Each cell has a unique 64-bit ID and can be subdivided into 4 child cells.
    """
    
    def __init__(self, min_level: int = 15, max_level: int = 15, max_cells: int = 8):
        """
        Initialize the S2 Cell Index.
        
        Args:
            min_level: Minimum cell level (smaller number = larger cells). Range: 0-30
            max_level: Maximum cell level (larger number = smaller cells). Range: 0-30
            max_cells: Maximum number of cells to return for a region
            
        Note: Level 15 cells are approximately 1km x 1km
              Level 13 cells are approximately 4km x 4km
              Level 17 cells are approximately 250m x 250m
        """
        self.min_level = min_level
        self.max_level = max_level
        self.max_cells = max_cells
        
        # Initialize region coverer for area queries
        self.coverer = RegionCoverer()
        self.coverer.min_level = min_level
        self.coverer.max_level = max_level
        self.coverer.max_cells = max_cells
    
    def get_cell_id(self, lat: float, lng: float) -> str:
        """
        Get the S2 cell ID for a given latitude/longitude point.
        
        Args:
            lat: Latitude in degrees
            lng: Longitude in degrees
            
        Returns:
            String representation of the cell ID (token)
        """
        latlng = LatLng.from_degrees(lat, lng)
        cell_id = CellId.from_lat_lng(latlng)
        
        # Get cell at the specified level
        cell_id = cell_id.parent(self.max_level)
        
        return cell_id.to_token()
    
    def get_cell_id_int(self, lat: float, lng: float) -> int:
        """
        Get the S2 cell ID as an integer for a given latitude/longitude point.
        
        Args:
            lat: Latitude in degrees
            lng: Longitude in degrees
            
        Returns:
            Integer representation of the cell ID
        """
        latlng = LatLng.from_degrees(lat, lng)
        cell_id = CellId.from_lat_lng(latlng)
        cell_id = cell_id.parent(self.max_level)
        
        return cell_id.id()
    
    def get_cell_bounds(self, cell_token: str) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Get the bounding box (lat/lng coordinates) of a cell.
        
        Args:
            cell_token: S2 cell token string
            
        Returns:
            Tuple of ((min_lat, min_lng), (max_lat, max_lng))
        """
        cell_id = CellId.from_token(cell_token)
        cell = Cell(cell_id)
        
        # Get the 4 vertices of the cell
        vertices = []
        for i in range(4):
            vertex = cell.get_vertex(i)
            latlng = LatLng.from_point(vertex)
            vertices.append((latlng.lat().degrees, latlng.lng().degrees))
        
        # Calculate bounding box
        lats = [v[0] for v in vertices]
        lngs = [v[1] for v in vertices]
        
        return ((min(lats), min(lngs)), (max(lats), max(lngs)))
    
    def get_cell_center(self, cell_token: str) -> Tuple[float, float]:
        """
        Get the center coordinates of a cell.
        
        Args:
            cell_token: S2 cell token string
            
        Returns:
            Tuple of (lat, lng) for the cell center
        """
        cell_id = CellId.from_token(cell_token)
        cell = Cell(cell_id)
        center = LatLng.from_point(cell.get_center())
        
        return (center.lat().degrees, center.lng().degrees)
    
    def get_neighbor_cells(self, cell_token: str) -> List[str]:
        """
        Get all neighboring cells (8 neighbors in cardinal and diagonal directions).
        
        Args:
            cell_token: S2 cell token string
            
        Returns:
            List of neighboring cell tokens
        """
        cell_id = CellId.from_token(cell_token)
        neighbors = []
        
        # Get edge neighbors (4 cardinal directions)
        for i in range(4):
            neighbor = cell_id.get_edge_neighbors()[i]
            neighbors.append(neighbor.to_token())
        
        # Get corner neighbors (4 diagonal directions)
        # This requires getting neighbors of neighbors
        all_neighbors_set = set(neighbors)
        for neighbor_token in neighbors[:4]:  # Only process edge neighbors
            neighbor_id = CellId.from_token(neighbor_token)
            for j in range(4):
                corner_neighbor = neighbor_id.get_edge_neighbors()[j]
                all_neighbors_set.add(corner_neighbor.to_token())
        
        # Remove the original cell if it was added
        all_neighbors_set.discard(cell_token)
        
        return list(all_neighbors_set)
    
    def get_cells_in_radius(self, lat: float, lng: float, radius_meters: float) -> List[str]:
        """
        Get all S2 cells within a given radius of a point.
        
        Args:
            lat: Center latitude in degrees
            lng: Center longitude in degrees
            radius_meters: Radius in meters
            
        Returns:
            List of cell tokens covering the area
        """
        center = LatLng.from_degrees(lat, lng)
        
        # Convert radius to angle (Earth radius = 6371000 meters)
        radius_radians = radius_meters / 6371000.0
        radius_angle = Angle.from_radians(radius_radians)
        
        # Create a cap region
        cap = Cap.from_axis_angle(center.to_point(), radius_angle)
        
        # Get cells covering this region
        covering = self.coverer.get_covering(cap)
        
        return [cell_id.to_token() for cell_id in covering]
    
    def get_cells_in_bbox(self, min_lat: float, min_lng: float, 
                          max_lat: float, max_lng: float) -> List[str]:
        """
        Get all S2 cells within a bounding box.
        
        Args:
            min_lat: Minimum latitude
            min_lng: Minimum longitude
            max_lat: Maximum latitude
            max_lng: Maximum longitude
            
        Returns:
            List of cell tokens covering the bounding box
        """
        # Create rectangle region from two corners
        lo = LatLng.from_degrees(min_lat, min_lng)
        hi = LatLng.from_degrees(max_lat, max_lng)
        rect = LatLngRect.from_point_pair(lo, hi)
        
        # Get cells covering this region
        covering = self.coverer.get_covering(rect)
        
        return [cell_id.to_token() for cell_id in covering]
    
    def get_cell_level(self, cell_token: str) -> int:
        """
        Get the level of a cell.
        
        Args:
            cell_token: S2 cell token string
            
        Returns:
            Cell level (0-30)
        """
        cell_id = CellId.from_token(cell_token)
        return cell_id.level()
    
    def get_parent_cell(self, cell_token: str, parent_level: int) -> str:
        """
        Get the parent cell at a specific level.
        
        Args:
            cell_token: S2 cell token string
            parent_level: Desired parent level
            
        Returns:
            Parent cell token
        """
        cell_id = CellId.from_token(cell_token)
        parent_id = cell_id.parent(parent_level)
        return parent_id.to_token()
    
    def get_child_cells(self, cell_token: str) -> List[str]:
        """
        Get the 4 child cells of a given cell.
        
        Args:
            cell_token: S2 cell token string
            
        Returns:
            List of 4 child cell tokens
        """
        cell_id = CellId.from_token(cell_token)
        children = []
        
        for i in range(4):
            child = cell_id.child(i)
            children.append(child.to_token())
        
        return children
