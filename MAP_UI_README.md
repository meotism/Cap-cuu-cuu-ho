# 🗺️ Vietnam Map Visualization - Interactive UI

Beautiful, interactive web-based map visualization for Vietnam using OpenStreetMap and S2 cells.

## 🌟 Features

### Interactive Map
- ✅ Full Vietnam map with OpenStreetMap tiles
- ✅ Click anywhere to get coordinates
- ✅ Smooth animations and transitions
- ✅ Zoom and pan controls
- ✅ Responsive design

### Major Cities
Quick navigation to major Vietnamese cities:
- 🏛️ **Hanoi** (Capital)
- 🌆 **Ho Chi Minh City**
- 🏖️ **Da Nang**
- ⚓ **Hai Phong**
- 🏯 **Hue**
- 🏝️ **Nha Trang**
- And more...

### S2 Cell Visualization
- 🔲 Draw S2 cells on the map
- 🏷️ Show/hide cell IDs
- ⚙️ Adjustable cell levels (10-17)
- 📊 Real-time statistics

### Road Data
- 🛣️ Fetch real roads from OpenStreetMap
- 🎨 Color-coded by road type (motorway, primary, etc.)
- ℹ️ Detailed road information in popups
- 📍 Road metadata (name, type, speed, one-way, etc.)

## 🚀 Quick Start

### Option 1: With Python Backend (Full Features)

1. **Start the server:**
   ```bash
   # Double-click the batch file
   start_map_server.bat
   
   # OR run manually
   python map_server.py
   ```

2. **Open your browser:**
   ```
   http://localhost:5000
   ```

3. **Explore the map:**
   - Click on city buttons to navigate
   - Draw S2 cells to see spatial indexing
   - Fetch real roads from OpenStreetMap

### Option 2: Standalone HTML (No Backend Required)

Simply open `vietnam_map_ui.html` directly in your browser:
- Double-click the file
- OR right-click → Open with → Your browser

**Note:** Without the backend, road fetching will show demo data instead of real OSM data.

## 📋 Prerequisites

- Python 3.7+ (for backend)
- Modern web browser (Chrome, Firefox, Edge, Safari)
- Internet connection (for map tiles and OSM data)

## 🎮 How to Use

### Navigate to Cities
1. Click any city button in the sidebar
2. Map will fly to that location with animation
3. A marker will be placed on the city

### Custom Location
1. Enter latitude and longitude in the inputs
2. Click "Go to Location"
3. Or click anywhere on the map to get coordinates

### Draw S2 Cells
1. Navigate to your area of interest
2. Choose cell level (10-17)
   - Level 13: ~4 km cells
   - Level 15: ~1 km cells (recommended)
   - Level 17: ~250 m cells
3. Click "Draw S2 Cells"
4. Toggle "Show Cell IDs" to see cell identifiers

### Fetch Roads
1. Navigate to your area of interest
2. Click "Fetch Roads from OSM"
3. Wait for data to load
4. Click on roads to see details

### Get Coordinates
- Click anywhere on the map
- A popup will show the coordinates
- Click "Use These Coordinates" to copy them to the input fields

## 🎨 Color Coding

Roads are color-coded by type:
- 🔴 **Red** - Motorways/Highways
- 🟠 **Orange** - Trunk roads
- 🟡 **Yellow** - Primary roads
- 🟢 **Green** - Secondary/Tertiary roads
- 🔵 **Blue** - Residential streets

## 🔧 API Endpoints (Backend)

### GET /
Main map UI page

### POST /api/fetch-roads
Fetch roads from OpenStreetMap
```json
{
  "min_lat": 21.0,
  "min_lng": 105.8,
  "max_lat": 21.1,
  "max_lng": 105.9
}
```

### POST /api/s2-cells
Get S2 cells for a bounding box
```json
{
  "min_lat": 21.0,
  "min_lng": 105.8,
  "max_lat": 21.1,
  "max_lng": 105.9,
  "cell_level": 15
}
```

### GET /api/cell-info
Get information about a cell
```
?lat=21.0285&lng=105.8542&level=15
```

### GET /api/vietnam-cities
Get list of major Vietnamese cities

### POST /api/load-area
Load and store map data for an area

### GET /api/query-location
Query stored road data at a location

### GET /api/health
Health check endpoint

## 📊 Statistics Panel

Real-time statistics showing:
- **S2 Cells**: Number of cells drawn
- **Roads**: Number of roads displayed
- **Markers**: Number of markers on map
- **Zoom Level**: Current map zoom level

## 🎯 Use Cases

### Urban Planning
- Visualize city road networks
- Analyze street layouts
- Identify road hierarchies

### Navigation Development
- Test routing algorithms
- Understand road connectivity
- Analyze turn restrictions

### Geographic Analysis
- Study spatial distribution
- Analyze area coverage
- Test location queries

### Education & Research
- Learn about S2 cells
- Understand map indexing
- Explore OpenStreetMap data

## 🌐 Technologies Used

- **Leaflet.js** - Interactive map library
- **OpenStreetMap** - Free map tiles and data
- **S2 Geometry** - Spatial indexing system
- **Flask** - Python web framework
- **HTML/CSS/JavaScript** - Frontend

## 🔍 Tips & Tricks

1. **Better Performance**: Use lower zoom levels when drawing many S2 cells
2. **Precise Cells**: Use level 17 for detailed analysis
3. **Large Areas**: Use level 13 for city-wide views
4. **Click and Explore**: Click on anything (cells, roads, map) to see details
5. **Keyboard Shortcuts**: Use +/- keys to zoom in/out

## 📱 Mobile Support

The interface is responsive and works on mobile devices:
- Touch to pan
- Pinch to zoom
- Tap on elements for details

## ⚙️ Configuration

### Change Default City
Edit `vietnam_map_ui.html` line ~745:
```javascript
goToCity('hanoi'); // Change to 'hcmc', 'danang', etc.
```

### Change Default Cell Level
Edit `vietnam_map_ui.html` line ~116:
```html
<input type="number" id="cellLevel" value="15" ...>
```

### Adjust Map Style
Edit the CSS section in `vietnam_map_ui.html` to customize colors, fonts, and layout.

## 🐛 Troubleshooting

### Roads not loading
- **Issue**: "Backend not available" error
- **Solution**: Make sure Flask server is running (`python map_server.py`)

### Cells not drawing
- **Issue**: Nothing happens when clicking "Draw S2 Cells"
- **Solution**: Make sure you're zoomed in enough. Try zoom level 12+

### Map tiles not loading
- **Issue**: Gray tiles or missing map
- **Solution**: Check your internet connection. OSM tiles require internet.

### Slow performance
- **Issue**: Browser becomes slow
- **Solution**: 
  - Clear existing cells before drawing new ones
  - Use lower cell levels for large areas
  - Zoom in to smaller areas

## 🔐 Privacy & Data

- All map tiles come from OpenStreetMap
- Road data is fetched from OSM Overpass API
- No personal data is collected or stored
- Data stays on your local machine

## 📝 Notes

- OSM Overpass API has rate limits (1 request/second)
- Large bbox queries may timeout
- Demo roads are shown when backend is unavailable
- Internet required for map tiles and OSM data

## 🎓 Learning Resources

- [Leaflet.js Documentation](https://leafletjs.com/)
- [OpenStreetMap Wiki](https://wiki.openstreetmap.org/)
- [S2 Geometry](http://s2geometry.io/)
- [Flask Documentation](https://flask.palletsprojects.com/)

## 🤝 Contributing

This is part of the Vietnam Map System project. See `MAP_README.md` for the full system documentation.

## ✨ Enjoy Exploring Vietnam's Map!

Have fun exploring the beautiful country of Vietnam through this interactive map visualization! 🇻🇳
