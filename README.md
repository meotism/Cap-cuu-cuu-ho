# 🆘 SOS Emergency Map System

Real-time emergency post system with Vietnam map integration using OpenStreetMap and Google S2 geometry.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python map_server.py
```
Or use the batch file:
```bash
start_map_server.bat
```

### 3. Open Browser
Navigate to: **http://localhost:5000**

## 📁 Project Structure

### Core Files (Essential)
- **map_server.py** - Flask web server with API endpoints
- **sos_database.py** - SQLite database for SOS posts
- **map_manager.py** - Map data coordinator
- **s2_cell_index.py** - S2 geometry spatial indexing
- **osm_data_fetcher.py** - OpenStreetMap data fetcher
- **road_segment_store.py** - Road data storage
- **vietnam_map_sos.html** - Main UI with SOS features
- **vietnam_map_ui.html** - Map-only UI (no SOS)
- **requirements.txt** - Python dependencies
- **start_map_server.bat** - Server launcher

### Data
- **map_data/** - SQLite database and cached map data

## 🌟 Features

### SOS Emergency System
- ✅ Create emergency posts with location
- ✅ Upload up to 5 images (base64 storage)
- ✅ Priority levels: Critical, High, Medium, Low
- ✅ Real-time updates (auto-refresh every 10 seconds)
- ✅ Interactive map with markers
- ✅ Offer help feature
- ✅ Search and statistics

### Map Features
- ✅ OpenStreetMap integration
- ✅ Google S2 cell indexing
- ✅ Road data fetching and storage
- ✅ Vietnam cities presets
- ✅ Spatial queries

## 🔧 API Endpoints

### Map APIs
- `POST /api/fetch-roads` - Fetch roads from OSM
- `POST /api/s2-cells` - Get S2 cells for area
- `GET /api/cell-info` - Get cell information
- `GET /api/vietnam-cities` - Get Vietnam cities list
- `POST /api/load-area` - Load and store map data
- `GET /api/query-location` - Query stored location

### SOS APIs
- `POST /api/sos/create` - Create new SOS post
- `GET /api/sos/recent` - Get recent posts (real-time)
- `POST /api/sos/area` - Get posts in geographic area
- `GET /api/sos/post/<id>` - Get specific post
- `PUT /api/sos/post/<id>/status` - Update post status
- `POST /api/sos/post/<id>/help` - Offer help
- `DELETE /api/sos/post/<id>` - Delete post
- `GET /api/sos/statistics` - Get statistics
- `GET /api/sos/search` - Search posts

## 📦 Dependencies

- **Flask 3.0.0** - Web framework
- **flask-cors 4.0.0** - CORS support
- **s2sphere 0.2.5** - S2 geometry library
- **overpy 0.7** - OSM Overpass API client
- **requests 2.31.0** - HTTP library

## 🎯 Usage

### Create SOS Post
1. Click "🆘 CREATE SOS POST" button
2. Click on the map to select location
3. Fill in details (title, description, priority)
4. Upload images (optional)
5. Submit

### View Posts
- Posts auto-refresh every 10 seconds
- Click markers to view details
- Click "Offer Help" to increment help count
- Color-coded by priority (red=critical, orange=high, yellow=medium, green=low)

## 🛠️ Development

### Database
SQLite database stored at `./map_data/sos_posts.db`

Tables:
- `sos_posts` - Emergency posts
- `sos_images` - Images (base64)

### S2 Cell Levels
- Level 10 (~220km) - Large regions
- Level 13 (~4km) - Cities
- Level 15 (~1km) - Default for indexing
- Level 17 (~250m) - High precision

## 📝 License

MIT License

## 🤝 Contributing

This is an emergency response system. Contributions welcome!
