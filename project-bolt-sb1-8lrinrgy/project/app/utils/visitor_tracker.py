import sqlite3
import json
from datetime import datetime, timedelta
import geoip2.database
import geoip2.errors
import requests
import os

class VisitorTracker:
    """Track website visitors with GeoIP lookup"""
    
    def __init__(self, db_path='visitors.db'):
        self.db_path = db_path
        self.geoip_db_path = 'GeoLite2-City.mmdb'
        self.geoip_reader = None
        
        # Initialize GeoIP database
        self._init_geoip()
    
    def _init_geoip(self):
        """Initialize GeoIP database"""
        try:
            if os.path.exists(self.geoip_db_path):
                self.geoip_reader = geoip2.database.Reader(self.geoip_db_path)
            else:
                print("GeoIP database not found. Geographic features will be limited.")
        except Exception as e:
            print(f"Error initializing GeoIP: {e}")
    
    def init_db(self):
        """Initialize SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS visits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    user_agent TEXT,
                    country_code TEXT,
                    country_name TEXT,
                    city TEXT,
                    latitude REAL,
                    longitude REAL
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_visits_timestamp 
                ON visits (timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_visits_ip 
                ON visits (ip_address)
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error initializing database: {e}")
    
    def track_visit(self, ip_address, user_agent=''):
        """Track a visitor and return visit statistics"""
        try:
            # Get geographic information
            geo_info = self._get_geo_info(ip_address)
            
            # Insert visit record
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO visits (ip_address, timestamp, user_agent, country_code, 
                                  country_name, city, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ip_address,
                datetime.now(),
                user_agent,
                geo_info.get('country_code'),
                geo_info.get('country_name'),
                geo_info.get('city'),
                geo_info.get('latitude'),
                geo_info.get('longitude')
            ))
            
            conn.commit()
            
            # Get visitor statistics
            stats = self._get_visitor_stats(cursor)
            
            conn.close()
            
            return {
                'total_visits': stats['total_visits'],
                'unique_visitors': stats['unique_visitors'],
                'recent_visits': stats['recent_visits'],
                'last_visitor': {
                    'country_code': geo_info.get('country_code'),
                    'country_name': geo_info.get('country_name'),
                    'city': geo_info.get('city')
                },
                'top_countries': stats['top_countries']
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_geo_info(self, ip_address):
        """Get geographic information for IP address"""
        geo_info = {
            'country_code': None,
            'country_name': None,
            'city': None,
            'latitude': None,
            'longitude': None
        }
        
        # Skip local IPs
        if ip_address in ['127.0.0.1', 'localhost'] or ip_address.startswith('192.168.'):
            geo_info.update({
                'country_code': 'TN',
                'country_name': 'Tunisia',
                'city': 'Tunis'
            })
            return geo_info
        
        try:
            if self.geoip_reader:
                response = self.geoip_reader.city(ip_address)
                geo_info.update({
                    'country_code': response.country.iso_code,
                    'country_name': response.country.name,
                    'city': response.city.name,
                    'latitude': float(response.location.latitude) if response.location.latitude else None,
                    'longitude': float(response.location.longitude) if response.location.longitude else None
                })
        except geoip2.errors.AddressNotFoundError:
            pass
        except Exception as e:
            print(f"GeoIP lookup error: {e}")
        
        return geo_info
    
    def _get_visitor_stats(self, cursor):
        """Get visitor statistics from database"""
        stats = {
            'total_visits': 0,
            'unique_visitors': 0,
            'recent_visits': 0,
            'top_countries': []
        }
        
        try:
            # Total visits
            cursor.execute('SELECT COUNT(*) FROM visits')
            stats['total_visits'] = cursor.fetchone()[0]
            
            # Unique visitors
            cursor.execute('SELECT COUNT(DISTINCT ip_address) FROM visits')
            stats['unique_visitors'] = cursor.fetchone()[0]
            
            # Recent visits (last 24 hours)
            yesterday = datetime.now() - timedelta(days=1)
            cursor.execute('SELECT COUNT(*) FROM visits WHERE timestamp > ?', (yesterday,))
            stats['recent_visits'] = cursor.fetchone()[0]
            
            # Top countries
            cursor.execute('''
                SELECT country_name, country_code, COUNT(*) as visit_count
                FROM visits 
                WHERE country_name IS NOT NULL
                GROUP BY country_name, country_code
                ORDER BY visit_count DESC
                LIMIT 5
            ''')
            
            stats['top_countries'] = [
                {
                    'name': row[0],
                    'code': row[1],
                    'visits': row[2]
                }
                for row in cursor.fetchall()
            ]
            
        except Exception as e:
            print(f"Error getting visitor stats: {e}")
        
        return stats
    
    def get_visit_history(self, days=7):
        """Get visit history for the last N days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            since_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                SELECT DATE(timestamp) as visit_date, COUNT(*) as visits
                FROM visits 
                WHERE timestamp > ?
                GROUP BY DATE(timestamp)
                ORDER BY visit_date
            ''', (since_date,))
            
            history = [
                {
                    'date': row[0],
                    'visits': row[1]
                }
                for row in cursor.fetchall()
            ]
            
            conn.close()
            return history
            
        except Exception as e:
            return []