"""
SOS Database Models

SQLite database for storing SOS posts with images and location data.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
import os
import base64


class SOSDatabase:
    """
    SQLite database manager for SOS emergency posts.
    
    Features:
    - Create SOS posts with location and images
    - Real-time post retrieval ordered by time
    - Image attachment support (stored as base64)
    - Geographic queries for nearby posts
    - Post status management
    """
    
    def __init__(self, db_path: str = "./map_data/sos_posts.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = db_path
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create SOS posts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sos_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                user_phone TEXT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                address TEXT,
                s2_cell_id TEXT,
                status TEXT DEFAULT 'active',
                priority TEXT DEFAULT 'medium',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                view_count INTEGER DEFAULT 0,
                help_count INTEGER DEFAULT 0
            )
        """)
        
        # Create images table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sos_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                image_data TEXT NOT NULL,
                image_type TEXT DEFAULT 'image/jpeg',
                image_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES sos_posts(id) ON DELETE CASCADE
            )
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sos_created_at 
            ON sos_posts(created_at DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sos_status 
            ON sos_posts(status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sos_location 
            ON sos_posts(latitude, longitude)
        """)
        
        conn.commit()
        conn.close()
        
        print(f"✓ SOS Database initialized: {self.db_path}")
    
    def create_post(self, user_name: str, title: str, description: str,
                   latitude: float, longitude: float,
                   user_phone: Optional[str] = None,
                   address: Optional[str] = None,
                   s2_cell_id: Optional[str] = None,
                   priority: str = 'medium',
                   images: Optional[List[Dict[str, Any]]] = None) -> int:
        """
        Create a new SOS post.
        
        Args:
            user_name: Name of the person posting
            title: Brief title of the emergency
            description: Detailed description
            latitude: Location latitude
            longitude: Location longitude
            user_phone: Optional phone number
            address: Optional address
            s2_cell_id: Optional S2 cell ID
            priority: Priority level (low, medium, high, critical)
            images: List of image dicts with 'data' (base64), 'type', 'name'
        
        Returns:
            ID of the created post
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert post
        cursor.execute("""
            INSERT INTO sos_posts 
            (user_name, user_phone, title, description, latitude, longitude,
             address, s2_cell_id, priority, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
        """, (user_name, user_phone, title, description, latitude, longitude,
              address, s2_cell_id, priority))
        
        post_id = cursor.lastrowid
        
        # Insert images if provided
        if images:
            for img in images:
                cursor.execute("""
                    INSERT INTO sos_images (post_id, image_data, image_type, image_name)
                    VALUES (?, ?, ?, ?)
                """, (post_id, img.get('data'), img.get('type', 'image/jpeg'),
                     img.get('name', f'image_{post_id}.jpg')))
        
        conn.commit()
        conn.close()
        
        print(f"✓ Created SOS post #{post_id}: {title}")
        return post_id
    
    def get_recent_posts(self, limit: int = 50, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent SOS posts ordered by creation time (newest first).
        
        Args:
            limit: Maximum number of posts to return
            status: Filter by status (active, resolved, cancelled)
        
        Returns:
            List of post dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT id, user_name, user_phone, title, description,
                   latitude, longitude, address, s2_cell_id,
                   status, priority, created_at, updated_at, resolved_at,
                   view_count, help_count
            FROM sos_posts
        """
        
        if status:
            query += " WHERE status = ?"
            cursor.execute(query + " ORDER BY created_at DESC LIMIT ?", (status, limit))
        else:
            cursor.execute(query + " ORDER BY created_at DESC LIMIT ?", (limit,))
        
        posts = []
        for row in cursor.fetchall():
            post = dict(row)
            
            # Get images for this post
            post['images'] = self._get_post_images(post['id'], conn)
            posts.append(post)
        
        conn.close()
        return posts
    
    def get_posts_in_area(self, min_lat: float, min_lng: float,
                         max_lat: float, max_lng: float,
                         status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get SOS posts within a geographic bounding box.
        
        Args:
            min_lat: Minimum latitude
            min_lng: Minimum longitude
            max_lat: Maximum latitude
            max_lng: Maximum longitude
            status: Filter by status
        
        Returns:
            List of posts in the area, ordered by time
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT id, user_name, user_phone, title, description,
                   latitude, longitude, address, s2_cell_id,
                   status, priority, created_at, updated_at, resolved_at,
                   view_count, help_count
            FROM sos_posts
            WHERE latitude BETWEEN ? AND ?
              AND longitude BETWEEN ? AND ?
        """
        
        params = [min_lat, max_lat, min_lng, max_lng]
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        
        posts = []
        for row in cursor.fetchall():
            post = dict(row)
            post['images'] = self._get_post_images(post['id'], conn)
            posts.append(post)
        
        conn.close()
        return posts
    
    def get_post_by_id(self, post_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific post by ID.
        
        Args:
            post_id: Post ID
        
        Returns:
            Post dictionary or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, user_name, user_phone, title, description,
                   latitude, longitude, address, s2_cell_id,
                   status, priority, created_at, updated_at, resolved_at,
                   view_count, help_count
            FROM sos_posts
            WHERE id = ?
        """, (post_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        post = dict(row)
        post['images'] = self._get_post_images(post_id, conn)
        
        # Increment view count
        cursor.execute("UPDATE sos_posts SET view_count = view_count + 1 WHERE id = ?", (post_id,))
        conn.commit()
        
        conn.close()
        return post
    
    def update_post_status(self, post_id: int, status: str) -> bool:
        """
        Update post status.
        
        Args:
            post_id: Post ID
            status: New status (active, resolved, cancelled)
        
        Returns:
            True if updated successfully
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        update_query = """
            UPDATE sos_posts 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
        """
        params = [status]
        
        if status == 'resolved':
            update_query += ", resolved_at = CURRENT_TIMESTAMP"
        
        update_query += " WHERE id = ?"
        params.append(post_id)
        
        cursor.execute(update_query, params)
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return success
    
    def increment_help_count(self, post_id: int) -> bool:
        """
        Increment help count (when someone offers help).
        
        Args:
            post_id: Post ID
        
        Returns:
            True if incremented successfully
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE sos_posts 
            SET help_count = help_count + 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (post_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_post(self, post_id: int) -> bool:
        """
        Delete a post and its images.
        
        Args:
            post_id: Post ID
        
        Returns:
            True if deleted successfully
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM sos_posts WHERE id = ?", (post_id,))
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return success
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total posts
        cursor.execute("SELECT COUNT(*) FROM sos_posts")
        total_posts = cursor.fetchone()[0]
        
        # Active posts
        cursor.execute("SELECT COUNT(*) FROM sos_posts WHERE status = 'active'")
        active_posts = cursor.fetchone()[0]
        
        # Resolved posts
        cursor.execute("SELECT COUNT(*) FROM sos_posts WHERE status = 'resolved'")
        resolved_posts = cursor.fetchone()[0]
        
        # Posts by priority
        cursor.execute("""
            SELECT priority, COUNT(*) as count 
            FROM sos_posts 
            WHERE status = 'active'
            GROUP BY priority
        """)
        priority_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Total images
        cursor.execute("SELECT COUNT(*) FROM sos_images")
        total_images = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_posts': total_posts,
            'active_posts': active_posts,
            'resolved_posts': resolved_posts,
            'priority_counts': priority_counts,
            'total_images': total_images
        }
    
    def _get_post_images(self, post_id: int, conn: sqlite3.Connection) -> List[Dict[str, str]]:
        """Get all images for a post."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, image_data, image_type, image_name, created_at
            FROM sos_images
            WHERE post_id = ?
            ORDER BY created_at
        """, (post_id,))
        
        images = []
        for row in cursor.fetchall():
            images.append({
                'id': row[0],
                'data': row[1],
                'type': row[2],
                'name': row[3],
                'created_at': row[4]
            })
        
        return images
    
    def search_posts(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search posts by keyword in title or description.
        
        Args:
            keyword: Search keyword
            limit: Maximum results
        
        Returns:
            List of matching posts
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, user_name, user_phone, title, description,
                   latitude, longitude, address, s2_cell_id,
                   status, priority, created_at, updated_at, resolved_at,
                   view_count, help_count
            FROM sos_posts
            WHERE title LIKE ? OR description LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (f'%{keyword}%', f'%{keyword}%', limit))
        
        posts = []
        for row in cursor.fetchall():
            post = dict(row)
            post['images'] = self._get_post_images(post['id'], conn)
            posts.append(post)
        
        conn.close()
        return posts


# Utility functions for image handling

def image_file_to_base64(file_path: str) -> str:
    """Convert image file to base64 string."""
    with open(file_path, 'rb') as f:
        image_data = f.read()
        return base64.b64encode(image_data).decode('utf-8')

def base64_to_image_file(base64_str: str, output_path: str):
    """Convert base64 string to image file."""
    image_data = base64.b64decode(base64_str)
    with open(output_path, 'wb') as f:
        f.write(image_data)
