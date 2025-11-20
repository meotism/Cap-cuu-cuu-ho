"""
OpenStreetMap Data Fetcher Module

This module provides functionality to query and retrieve map data from
OpenStreetMap using the Overpass API.
"""

import overpy
import time
from typing import List, Dict, Tuple, Optional, Any
import requests


class OSMDataFetcher:
    """
    Fetches map data from OpenStreetMap using the Overpass API.
    
    The Overpass API allows querying OSM data with a powerful query language.
    This class provides convenient methods for fetching roads, intersections,
    and other map features.
    """
    
    def __init__(self, endpoint: str = "https://overpass-api.de/api/interpreter",
                 timeout: int = 60, max_retries: int = 3):
        """
        Initialize the OSM Data Fetcher.
        
        Args:
            endpoint: Overpass API endpoint URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
        """
        self.api = overpy.Overpass(url=endpoint)
        self.timeout = timeout
        self.max_retries = max_retries
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum seconds between requests (rate limiting)
    
    def _rate_limit(self):
        """Enforce rate limiting between API requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _execute_query(self, query: str) -> overpy.Result:
        """
        Execute an Overpass query with retry logic.
        
        Args:
            query: Overpass QL query string
            
        Returns:
            Query result
        """
        for attempt in range(self.max_retries):
            try:
                self._rate_limit()
                result = self.api.query(query)
                return result
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    print(f"Query failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise
    
    def get_roads_in_bbox(self, min_lat: float, min_lng: float,
                          max_lat: float, max_lng: float,
                          road_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Fetch all roads within a bounding box.
        
        Args:
            min_lat: Minimum latitude
            min_lng: Minimum longitude
            max_lat: Maximum latitude
            max_lng: Maximum longitude
            road_types: List of highway types to filter (e.g., ['motorway', 'primary', 'secondary'])
                       If None, fetches all road types
            
        Returns:
            Dictionary containing ways (roads), nodes, and metadata
        """
        # Build highway type filter
        if road_types:
            highway_filter = '|'.join(road_types)
            highway_query = f'["highway"~"{highway_filter}"]'
        else:
            highway_query = '["highway"]'
        
        # Overpass QL query
        query = f"""
        [out:json][timeout:{self.timeout}];
        (
          way{highway_query}({min_lat},{min_lng},{max_lat},{max_lng});
        );
        out body;
        >;
        out skel qt;
        """
        
        result = self._execute_query(query)
        
        # Parse result into structured format
        roads = []
        nodes_dict = {}
        
        # Process nodes
        for node in result.nodes:
            nodes_dict[node.id] = {
                'id': node.id,
                'lat': float(node.lat),
                'lng': float(node.lon),
                'tags': dict(node.tags)
            }
        
        # Process ways (roads)
        for way in result.ways:
            road = {
                'id': way.id,
                'tags': dict(way.tags),
                'nodes': [node.id for node in way.nodes],
                'node_coords': [(nodes_dict[node.id]['lat'], nodes_dict[node.id]['lng']) 
                               for node in way.nodes if node.id in nodes_dict]
            }
            roads.append(road)
        
        return {
            'roads': roads,
            'nodes': nodes_dict,
            'bbox': {
                'min_lat': min_lat,
                'min_lng': min_lng,
                'max_lat': max_lat,
                'max_lng': max_lng
            }
        }
    
    def get_roads_around_point(self, lat: float, lng: float, 
                               radius_meters: float,
                               road_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Fetch all roads within a radius of a point.
        
        Args:
            lat: Center latitude
            lng: Center longitude
            radius_meters: Search radius in meters
            road_types: List of highway types to filter
            
        Returns:
            Dictionary containing ways (roads), nodes, and metadata
        """
        # Build highway type filter
        if road_types:
            highway_filter = '|'.join(road_types)
            highway_query = f'["highway"~"{highway_filter}"]'
        else:
            highway_query = '["highway"]'
        
        # Overpass QL query with around filter
        query = f"""
        [out:json][timeout:{self.timeout}];
        (
          way{highway_query}(around:{radius_meters},{lat},{lng});
        );
        out body;
        >;
        out skel qt;
        """
        
        result = self._execute_query(query)
        
        # Parse result (same as bbox method)
        roads = []
        nodes_dict = {}
        
        for node in result.nodes:
            nodes_dict[node.id] = {
                'id': node.id,
                'lat': float(node.lat),
                'lng': float(node.lon),
                'tags': dict(node.tags)
            }
        
        for way in result.ways:
            road = {
                'id': way.id,
                'tags': dict(way.tags),
                'nodes': [node.id for node in way.nodes],
                'node_coords': [(nodes_dict[node.id]['lat'], nodes_dict[node.id]['lng']) 
                               for node in way.nodes if node.id in nodes_dict]
            }
            roads.append(road)
        
        return {
            'roads': roads,
            'nodes': nodes_dict,
            'center': {'lat': lat, 'lng': lng},
            'radius_meters': radius_meters
        }
    
    def get_road_by_id(self, way_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific road by its OSM way ID.
        
        Args:
            way_id: OpenStreetMap way ID
            
        Returns:
            Road data dictionary or None if not found
        """
        query = f"""
        [out:json][timeout:{self.timeout}];
        way({way_id});
        out body;
        >;
        out skel qt;
        """
        
        try:
            result = self._execute_query(query)
            
            if not result.ways:
                return None
            
            # Get nodes
            nodes_dict = {}
            for node in result.nodes:
                nodes_dict[node.id] = {
                    'id': node.id,
                    'lat': float(node.lat),
                    'lng': float(node.lon),
                    'tags': dict(node.tags)
                }
            
            # Get way
            way = result.ways[0]
            return {
                'id': way.id,
                'tags': dict(way.tags),
                'nodes': [node.id for node in way.nodes],
                'node_coords': [(nodes_dict[node.id]['lat'], nodes_dict[node.id]['lng']) 
                               for node in way.nodes if node.id in nodes_dict]
            }
        except Exception as e:
            print(f"Error fetching road {way_id}: {e}")
            return None
    
    def get_turn_restrictions(self, min_lat: float, min_lng: float,
                             max_lat: float, max_lng: float) -> List[Dict[str, Any]]:
        """
        Fetch turn restrictions within a bounding box.
        
        Turn restrictions are stored as relations in OSM with type='restriction'.
        
        Args:
            min_lat: Minimum latitude
            min_lng: Minimum longitude
            max_lat: Maximum latitude
            max_lng: Maximum longitude
            
        Returns:
            List of turn restriction dictionaries
        """
        query = f"""
        [out:json][timeout:{self.timeout}];
        (
          relation["type"="restriction"]({min_lat},{min_lng},{max_lat},{max_lng});
        );
        out body;
        >;
        out skel qt;
        """
        
        result = self._execute_query(query)
        
        restrictions = []
        for relation in result.relations:
            restriction = {
                'id': relation.id,
                'tags': dict(relation.tags),
                'members': []
            }
            
            for member in relation.members:
                # Get member type - overpy uses _type_value attribute
                member_type = getattr(member, '_type_value', None) or member.__class__.__name__.replace('Relation', '').lower()
                
                restriction['members'].append({
                    'type': member_type,
                    'ref': member.ref,
                    'role': member.role
                })
            
            restrictions.append(restriction)
        
        return restrictions
    
    def get_intersections(self, min_lat: float, min_lng: float,
                         max_lat: float, max_lng: float) -> List[Dict[str, Any]]:
        """
        Find road intersections (nodes where multiple roads meet).
        
        Args:
            min_lat: Minimum latitude
            min_lng: Minimum longitude
            max_lat: Maximum latitude
            max_lng: Maximum longitude
            
        Returns:
            List of intersection nodes with their connected roads
        """
        # First, get all roads in the area
        roads_data = self.get_roads_in_bbox(min_lat, min_lng, max_lat, max_lng)
        
        # Count how many roads use each node
        node_usage = {}
        for road in roads_data['roads']:
            for node_id in road['nodes']:
                if node_id not in node_usage:
                    node_usage[node_id] = []
                node_usage[node_id].append(road['id'])
        
        # Intersections are nodes used by 3+ roads (or 2+ different roads)
        intersections = []
        for node_id, road_ids in node_usage.items():
            if len(set(road_ids)) >= 2:  # At least 2 different roads meet here
                if node_id in roads_data['nodes']:
                    node_data = roads_data['nodes'][node_id]
                    intersections.append({
                        'node_id': node_id,
                        'lat': node_data['lat'],
                        'lng': node_data['lng'],
                        'connected_roads': list(set(road_ids)),
                        'tags': node_data['tags']
                    })
        
        return intersections
    
    @staticmethod
    def parse_road_metadata(road: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract useful metadata from road tags.
        
        Args:
            road: Road dictionary with 'tags' field
            
        Returns:
            Parsed metadata dictionary
        """
        tags = road.get('tags', {})
        
        metadata = {
            'name': tags.get('name', 'Unnamed'),
            'highway_type': tags.get('highway', 'unknown'),
            'oneway': tags.get('oneway', 'no') in ['yes', '1', 'true'],
            'maxspeed': tags.get('maxspeed'),
            'lanes': tags.get('lanes'),
            'surface': tags.get('surface'),
            'access': tags.get('access'),
            'bridge': tags.get('bridge') == 'yes',
            'tunnel': tags.get('tunnel') == 'yes',
            'toll': tags.get('toll') == 'yes',
            'ref': tags.get('ref'),  # Road number/reference
        }
        
        return metadata
