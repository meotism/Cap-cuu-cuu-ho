"""
Check if all required packages are installed for SOS Emergency Map Server
"""

import sys

def check_imports():
    """Check if all required packages can be imported."""
    required_packages = {
        'flask': 'Flask',
        'flask_cors': 'Flask-CORS',
        'flask_socketio': 'Flask-SocketIO',
        's2sphere': 'S2 Geometry',
        'overpy': 'OverPy (OSM API)',
        'requests': 'Requests',
        'sqlite3': 'SQLite3 (built-in)',
        'json': 'JSON (built-in)',
        'os': 'OS (built-in)',
        'base64': 'Base64 (built-in)'
    }
    
    print("=" * 60)
    print("🔍 Checking Required Packages")
    print("=" * 60)
    print()
    
    all_ok = True
    
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"✅ {name:<30} OK")
        except ImportError as e:
            print(f"❌ {name:<30} MISSING")
            all_ok = False
    
    print()
    print("=" * 60)
    
    if all_ok:
        print("✅ All required packages are installed!")
        print()
        print("You can now run the server:")
        print("  Windows: start_server.bat")
        print("  Linux:   ./start_server.sh")
        print("=" * 60)
        return 0
    else:
        print("❌ Some packages are missing!")
        print()
        print("Install missing packages:")
        print("  pip install -r requirements.txt")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(check_imports())
