"""
Flask Web Server for Vietnam Map Visualization

This server provides APIs to fetch map data and serve the HTML interface.
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from map_manager import MapManager
from sos_database import SOSDatabase
import os
import base64

app = Flask(__name__)
CORS(app)  # Enable CORS for API requests

# Initialize map manager
map_manager = MapManager(cell_level=15, storage_dir="./map_data")

# Initialize SOS database
sos_db = SOSDatabase(db_path="./map_data/sos_posts.db")

@app.route('/')
def index():
    """Serve the main HTML page with SOS feature."""
    return send_file('vietnam_map_sos.html')

@app.route('/map-only')
def map_only():
    """Serve the map-only page without SOS."""
    return send_file('vietnam_map_ui.html')

@app.route('/api/fetch-roads', methods=['POST'])
def fetch_roads():
    """
    Fetch roads from OpenStreetMap for a given bounding box.
    
    Request JSON:
    {
        "min_lat": float,
        "min_lng": float,
        "max_lat": float,
        "max_lng": float
    }
    
    Returns:
    {
        "roads": [...],
        "stats": {...}
    }
    """
    try:
        data = request.json
        min_lat = float(data['min_lat'])
        min_lng = float(data['min_lng'])
        max_lat = float(data['max_lat'])
        max_lng = float(data['max_lng'])
        
        print(f"Fetching roads for bbox: ({min_lat}, {min_lng}) to ({max_lat}, {max_lng})")
        
        # Fetch roads from OSM
        from osm_data_fetcher import OSMDataFetcher
        fetcher = OSMDataFetcher()
        
        roads_data = fetcher.get_roads_in_bbox(
            min_lat, min_lng, max_lat, max_lng,
            road_types=['motorway', 'trunk', 'primary', 'secondary', 'tertiary']
        )
        
        # Parse metadata for each road
        for road in roads_data['roads']:
            road['metadata'] = OSMDataFetcher.parse_road_metadata(road)
        
        print(f"Fetched {len(roads_data['roads'])} roads")
        
        return jsonify({
            'roads': roads_data['roads'],
            'stats': {
                'total_roads': len(roads_data['roads']),
                'total_nodes': len(roads_data['nodes'])
            }
        })
        
    except Exception as e:
        print(f"Error fetching roads: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/s2-cells', methods=['POST'])
def get_s2_cells():
    """
    Get S2 cells for a bounding box.
    
    Request JSON:
    {
        "min_lat": float,
        "min_lng": float,
        "max_lat": float,
        "max_lng": float,
        "cell_level": int (optional, default 15)
    }
    
    Returns:
    {
        "cells": [...],
        "count": int
    }
    """
    try:
        data = request.json
        min_lat = float(data['min_lat'])
        min_lng = float(data['min_lng'])
        max_lat = float(data['max_lat'])
        max_lng = float(data['max_lng'])
        cell_level = int(data.get('cell_level', 15))
        
        from s2_cell_index import S2CellIndex
        s2 = S2CellIndex(min_level=cell_level, max_level=cell_level)
        
        # Get cells in bbox
        cell_tokens = s2.get_cells_in_bbox(min_lat, min_lng, max_lat, max_lng)
        
        # Get details for each cell
        cells = []
        for token in cell_tokens:
            center = s2.get_cell_center(token)
            bounds = s2.get_cell_bounds(token)
            
            cells.append({
                'token': token,
                'center': {'lat': center[0], 'lng': center[1]},
                'bounds': {
                    'sw': {'lat': bounds[0][0], 'lng': bounds[0][1]},
                    'ne': {'lat': bounds[1][0], 'lng': bounds[1][1]}
                },
                'level': cell_level
            })
        
        return jsonify({
            'cells': cells,
            'count': len(cells)
        })
        
    except Exception as e:
        print(f"Error getting S2 cells: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cell-info', methods=['GET'])
def get_cell_info():
    """
    Get information about a specific location's S2 cell.
    
    Query params:
    - lat: latitude
    - lng: longitude
    - level: cell level (optional, default 15)
    
    Returns:
    {
        "cell_token": str,
        "center": {...},
        "bounds": {...},
        "neighbors": [...]
    }
    """
    try:
        lat = float(request.args.get('lat'))
        lng = float(request.args.get('lng'))
        level = int(request.args.get('level', 15))
        
        from s2_cell_index import S2CellIndex
        s2 = S2CellIndex(min_level=level, max_level=level)
        
        # Get cell info
        cell_token = s2.get_cell_id(lat, lng)
        center = s2.get_cell_center(cell_token)
        bounds = s2.get_cell_bounds(cell_token)
        neighbors = s2.get_neighbor_cells(cell_token)
        
        return jsonify({
            'cell_token': cell_token,
            'center': {'lat': center[0], 'lng': center[1]},
            'bounds': {
                'sw': {'lat': bounds[0][0], 'lng': bounds[0][1]},
                'ne': {'lat': bounds[1][0], 'lng': bounds[1][1]}
            },
            'neighbors': neighbors,
            'level': level
        })
        
    except Exception as e:
        print(f"Error getting cell info: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/vietnam-cities', methods=['GET'])
def get_vietnam_cities():
    """Get list of major Vietnam cities with coordinates."""
    cities = [
        {'id': 'hanoi', 'name': 'Hanoi', 'lat': 21.0285, 'lng': 105.8542, 'description': 'Capital of Vietnam'},
        {'id': 'hcmc', 'name': 'Ho Chi Minh City', 'lat': 10.8231, 'lng': 106.6297, 'description': 'Largest city'},
        {'id': 'danang', 'name': 'Da Nang', 'lat': 16.0544, 'lng': 108.2022, 'description': 'Central coastal city'},
        {'id': 'haiphong', 'name': 'Hai Phong', 'lat': 20.8449, 'lng': 106.6881, 'description': 'Major port city'},
        {'id': 'hue', 'name': 'Hue', 'lat': 16.4637, 'lng': 107.5909, 'description': 'Imperial city'},
        {'id': 'nhatrang', 'name': 'Nha Trang', 'lat': 12.2388, 'lng': 109.1967, 'description': 'Beach resort city'},
        {'id': 'cantho', 'name': 'Can Tho', 'lat': 10.0452, 'lng': 105.7469, 'description': 'Mekong Delta hub'},
        {'id': 'vungtau', 'name': 'Vung Tau', 'lat': 10.3460, 'lng': 107.0843, 'description': 'Coastal city'},
        {'id': 'dalat', 'name': 'Da Lat', 'lat': 11.9404, 'lng': 108.4583, 'description': 'Highland resort town'},
        {'id': 'halong', 'name': 'Ha Long', 'lat': 20.9601, 'lng': 107.0432, 'description': 'UNESCO World Heritage Bay'}
    ]
    return jsonify({'cities': cities})

@app.route('/api/load-area', methods=['POST'])
def load_area():
    """
    Load and index map data for an area (saves to storage).
    
    Request JSON:
    {
        "min_lat": float,
        "min_lng": float,
        "max_lat": float,
        "max_lng": float,
        "road_types": [str] (optional)
    }
    
    Returns:
    {
        "success": bool,
        "stats": {...}
    }
    """
    try:
        data = request.json
        min_lat = float(data['min_lat'])
        min_lng = float(data['min_lng'])
        max_lat = float(data['max_lat'])
        max_lng = float(data['max_lng'])
        road_types = data.get('road_types')
        
        print(f"Loading map data for area...")
        
        stats = map_manager.load_map_data_bbox(
            min_lat, min_lng, max_lat, max_lng,
            road_types=road_types
        )
        
        print(f"Loaded: {stats}")
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        print(f"Error loading area: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/query-location', methods=['GET'])
def query_location():
    """
    Query roads at a specific location from stored data.
    
    Query params:
    - lat: latitude
    - lng: longitude
    
    Returns stored road data for that location's cell.
    """
    try:
        lat = float(request.args.get('lat'))
        lng = float(request.args.get('lng'))
        
        result = map_manager.query_roads_at_location(lat, lng)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error querying location: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'Vietnam Map Server',
        'version': '1.0.0'
    })

# ============================================================================
# SOS EMERGENCY POSTS API
# ============================================================================

@app.route('/api/sos/create', methods=['POST'])
def create_sos_post():
    """
    Create a new SOS emergency post.
    
    Request JSON:
    {
        "user_name": str,
        "title": str,
        "description": str,
        "latitude": float,
        "longitude": float,
        "user_phone": str (optional),
        "address": str (optional),
        "priority": str (optional: low, medium, high, critical),
        "images": [{
            "data": "base64_string",
            "type": "image/jpeg",
            "name": "filename.jpg"
        }] (optional)
    }
    """
    try:
        data = request.json
        
        # Calculate S2 cell ID
        from s2_cell_index import S2CellIndex
        s2 = S2CellIndex(min_level=15, max_level=15)
        s2_cell_id = s2.get_cell_id(data['latitude'], data['longitude'])
        
        # Create post
        post_id = sos_db.create_post(
            user_name=data['user_name'],
            title=data['title'],
            description=data['description'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            user_phone=data.get('user_phone'),
            address=data.get('address'),
            s2_cell_id=s2_cell_id,
            priority=data.get('priority', 'medium'),
            images=data.get('images', [])
        )
        
        return jsonify({
            'success': True,
            'post_id': post_id,
            'message': 'SOS post created successfully'
        })
        
    except Exception as e:
        print(f"Error creating SOS post: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/sos/recent', methods=['GET'])
def get_recent_sos_posts():
    """
    Get recent SOS posts (real-time, ordered by time).
    
    Query params:
    - limit: Maximum posts to return (default 50)
    - status: Filter by status (active, resolved, cancelled)
    """
    try:
        limit = int(request.args.get('limit', 50))
        status = request.args.get('status')
        
        posts = sos_db.get_recent_posts(limit=limit, status=status)
        
        return jsonify({
            'posts': posts,
            'count': len(posts)
        })
        
    except Exception as e:
        print(f"Error getting recent posts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sos/area', methods=['POST'])
def get_sos_in_area():
    """
    Get SOS posts in a geographic area.
    
    Request JSON:
    {
        "min_lat": float,
        "min_lng": float,
        "max_lat": float,
        "max_lng": float,
        "status": str (optional)
    }
    """
    try:
        data = request.json
        
        posts = sos_db.get_posts_in_area(
            min_lat=data['min_lat'],
            min_lng=data['min_lng'],
            max_lat=data['max_lat'],
            max_lng=data['max_lng'],
            status=data.get('status')
        )
        
        return jsonify({
            'posts': posts,
            'count': len(posts)
        })
        
    except Exception as e:
        print(f"Error getting posts in area: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sos/post/<int:post_id>', methods=['GET'])
def get_sos_post(post_id):
    """Get a specific SOS post by ID."""
    try:
        post = sos_db.get_post_by_id(post_id)
        
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        return jsonify({'post': post})
        
    except Exception as e:
        print(f"Error getting post: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sos/post/<int:post_id>/status', methods=['PUT'])
def update_sos_status(post_id):
    """
    Update SOS post status.
    
    Request JSON:
    {
        "status": "resolved" | "cancelled" | "active"
    }
    """
    try:
        data = request.json
        status = data.get('status')
        
        if not status:
            return jsonify({'error': 'Status is required'}), 400
        
        success = sos_db.update_post_status(post_id, status)
        
        if not success:
            return jsonify({'error': 'Post not found'}), 404
        
        return jsonify({
            'success': True,
            'message': f'Post status updated to {status}'
        })
        
    except Exception as e:
        print(f"Error updating status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sos/post/<int:post_id>/help', methods=['POST'])
def offer_help(post_id):
    """Increment help count (someone offering help)."""
    try:
        success = sos_db.increment_help_count(post_id)
        
        if not success:
            return jsonify({'error': 'Post not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Help count incremented'
        })
        
    except Exception as e:
        print(f"Error offering help: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sos/post/<int:post_id>', methods=['DELETE'])
def delete_sos_post(post_id):
    """Delete a SOS post."""
    try:
        success = sos_db.delete_post(post_id)
        
        if not success:
            return jsonify({'error': 'Post not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Post deleted successfully'
        })
        
    except Exception as e:
        print(f"Error deleting post: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sos/statistics', methods=['GET'])
def get_sos_statistics():
    """Get SOS database statistics."""
    try:
        stats = sos_db.get_statistics()
        return jsonify({'statistics': stats})
        
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sos/search', methods=['GET'])
def search_sos_posts():
    """
    Search SOS posts by keyword.
    
    Query params:
    - q: Search query
    - limit: Maximum results (default 50)
    """
    try:
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 50))
        
        if not query:
            return jsonify({'error': 'Search query required'}), 400
        
        posts = sos_db.search_posts(query, limit=limit)
        
        return jsonify({
            'posts': posts,
            'count': len(posts),
            'query': query
        })
        
    except Exception as e:
        print(f"Error searching posts: {e}")
        return jsonify({'error': str(e)}), 500

def main():
    """Start the Flask server."""
    print("=" * 60)
    print("🌏 VIETNAM MAP SERVER")
    print("=" * 60)
    print()
    print("Starting Flask server...")
    print()
    print("📍 Server URL: http://localhost:5000")
    print("🌐 Open your browser and navigate to: http://localhost:5000")
    print()
    print("Available endpoints:")
    print("  GET  /                    - Map visualization UI")
    print("  POST /api/fetch-roads     - Fetch roads from OSM")
    print("  POST /api/s2-cells        - Get S2 cells for area")
    print("  GET  /api/cell-info       - Get info about a cell")
    print("  GET  /api/vietnam-cities  - Get Vietnam cities list")
    print("  POST /api/load-area       - Load and store map data")
    print("  GET  /api/query-location  - Query stored location data")
    print("  GET  /api/health          - Health check")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    # Start the server
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()
