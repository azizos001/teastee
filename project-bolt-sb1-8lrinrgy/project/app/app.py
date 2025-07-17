import os
import json
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO, emit
import threading
import time
import requests
from utils.system_monitor import SystemMonitor
from utils.docker_monitor import DockerMonitor
from utils.visitor_tracker import VisitorTracker

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Initialize rate limiter
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize monitoring components
system_monitor = SystemMonitor()
docker_monitor = DockerMonitor()
visitor_tracker = VisitorTracker()

# Global variables for caching
cached_system_stats = {}
cached_services = []
last_update = datetime.now()

def update_system_data():
    """Background task to update system data every 10 seconds"""
    global cached_system_stats, cached_services, last_update
    
    while True:
        try:
            # Update system stats
            cached_system_stats = system_monitor.get_system_stats()
            
            # Update services
            cached_services = docker_monitor.get_running_containers()
            
            last_update = datetime.now()
            
            # Emit to all connected clients
            socketio.emit('system_update', {
                'stats': cached_system_stats,
                'services': cached_services,
                'timestamp': last_update.isoformat()
            })
            
        except Exception as e:
            print(f"Error updating system data: {e}")
        
        time.sleep(10)

# Start background thread
update_thread = threading.Thread(target=update_system_data, daemon=True)
update_thread.start()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/system')
def get_system_stats():
    """Get current system statistics"""
    return jsonify(cached_system_stats)

@app.route('/api/services')
def get_services():
    """Get running Docker services"""
    return jsonify(cached_services)

@app.route('/api/projects')
def get_projects():
    """Get projects list"""
    try:
        with open('static/projects.json', 'r') as f:
            projects = json.load(f)
        return jsonify(projects)
    except FileNotFoundError:
        return jsonify([])

@app.route('/api/visit', methods=['POST'])
@limiter.limit("10 per minute")
def track_visit():
    """Track page visit"""
    try:
        ip = request.headers.get('X-Real-IP', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        
        visit_data = visitor_tracker.track_visit(ip, user_agent)
        return jsonify(visit_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/weather')
def get_weather():
    """Get weather data for Tunisia"""
    try:
        api_key = os.environ.get('OPENWEATHER_API_KEY')
        if not api_key:
            return jsonify({'error': 'API key not configured'}), 500
        
        url = f"http://api.openweathermap.org/data/2.5/weather?q=Tunis,TN&appid={api_key}&units=metric"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'temperature': data['main']['temp'],
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon']
            })
        else:
            return jsonify({'error': 'Weather data unavailable'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('system_update', {
        'stats': cached_system_stats,
        'services': cached_services,
        'timestamp': last_update.isoformat()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Create database tables
    visitor_tracker.init_db()
    
    # Run the application
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)