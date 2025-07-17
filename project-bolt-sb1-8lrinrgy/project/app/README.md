# Aziz's Home Lab Dashboard ⚡

A beautiful, real-time dashboard for monitoring self-hosted services and system statistics. Built with Flask, Tailwind CSS, and Chart.js.

## Features

- **Real-time System Monitoring**: CPU, Memory, Disk, and Network usage with live charts
- **Docker Container Management**: Monitor running services with status, uptime, and resource usage
- **Project Showcase**: Display your portfolio projects with GitHub integration
- **Visitor Analytics**: Track page visits with geographic information
- **Weather Integration**: Current weather display for Tunisia
- **Responsive Design**: Mobile-first approach with dark theme
- **WebSocket Updates**: Real-time data updates without page refresh

## Tech Stack

- **Backend**: Python 3.11 + Flask + Socket.IO
- **Frontend**: HTML5 + Tailwind CSS 3 + Chart.js
- **Database**: SQLite
- **Monitoring**: psutil (system) + Docker SDK (containers)
- **Deployment**: Docker + Nginx reverse proxy

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- OpenWeather API key (optional, for weather data)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/azizbenabdallah/homelab-dashboard.git
   cd homelab-dashboard
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the dashboard**
   - Local: http://localhost:8080
   - Production: https://si-aziz-home.duckdns.org

### Development Setup

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the development server**
   ```bash
   python app.py
   ```

3. **Access at http://localhost:5000**

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | `dev-secret-key` |
| `OPENWEATHER_API_KEY` | OpenWeather API key | None |
| `DATABASE_URL` | SQLite database path | `sqlite:///data/homelab.db` |
| `FLASK_ENV` | Flask environment | `production` |
| `LOG_LEVEL` | Logging level | `INFO` |

### API Keys

1. **OpenWeather API**: Get your free API key at https://openweathermap.org/api
2. **GeoIP Database**: Download GeoLite2-City.mmdb from MaxMind (optional)

## API Endpoints

- `GET /` - Main dashboard
- `GET /api/system` - System statistics
- `GET /api/services` - Docker services
- `GET /api/projects` - Project list
- `POST /api/visit` - Track visitor
- `GET /api/weather` - Weather data

## Docker Deployment

### With Docker Compose (Recommended)

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Docker Build

```bash
# Build image
docker build -t homelab-dashboard .

# Run container
docker run -d \
  --name homelab-dashboard \
  -p 8080:5000 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v $(pwd)/data:/app/data \
  homelab-dashboard
```

## Nginx Configuration

For production deployment with SSL:

```nginx
server {
    listen 80;
    server_name si-aziz-home.duckdns.org;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name si-aziz-home.duckdns.org;
    
    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Customization

### Adding Projects

Edit `static/projects.json` to add your projects:

```json
{
    "title": "My Project",
    "icon": "🚀",
    "description": "Project description",
    "technologies": ["Python", "Docker"],
    "github": "https://github.com/username/project"
}
```

### Styling

- Modify `static/css/style.css` for custom styles
- Update color scheme in `tailwind.config` section
- Add animations in `static/js/dashboard.js`

## Performance Optimization

- **Caching**: Static files cached for 1 year
- **Compression**: Gzip enabled for all text content
- **Rate Limiting**: API endpoints protected
- **WebSocket**: Efficient real-time updates
- **Lazy Loading**: Charts update without full refresh

## Security Features

- Rate limiting on all endpoints
- Input validation and sanitization
- CORS headers configured
- Docker socket read-only access
- No sensitive data in logs

## Monitoring

### Health Checks

- Container health check: `curl -f http://localhost:5000/api/system`
- Nginx health check: `curl -f http://localhost:8080/health`

### Logs

```bash
# Application logs
docker-compose logs web

# Nginx logs
docker-compose logs nginx

# All logs
docker-compose logs -f
```

## Troubleshooting

### Common Issues

1. **Docker socket permission denied**
   ```bash
   sudo usermod -aG docker $USER
   # Logout and login again
   ```

2. **Port already in use**
   ```bash
   # Change port in docker-compose.yml
   ports:
     - "8081:80"  # Instead of 8080:80
   ```

3. **Memory issues**
   ```bash
   # Increase Docker memory limit
   # Or reduce chart data retention in dashboard.js
   ```

### Debug Mode

```bash
# Run in debug mode
FLASK_ENV=development python app.py

# Enable verbose logging
LOG_LEVEL=DEBUG docker-compose up
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Credits

- **Developer**: Aziz Benabdallah
- **Icons**: Lucide React
- **Charts**: Chart.js
- **Framework**: Flask + Tailwind CSS
- **Monitoring**: psutil + Docker SDK

## TODO

- [ ] Add SSL/TLS certificate automation
- [ ] Implement user authentication
- [ ] Add more system metrics
- [ ] Create mobile app
- [ ] Add alert notifications
- [ ] Database migration system
- [ ] Multi-language support
- [ ] Theme customization
- [ ] Backup/restore functionality
- [ ] Performance benchmarking

---

**Made with ❤️ in Tunisia**