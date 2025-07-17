// Dashboard JavaScript for Aziz's Home Lab
class Dashboard {
    constructor() {
        this.socket = null;
        this.charts = {};
        this.systemData = {
            cpu: [],
            memory: [],
            network: { rx: [], tx: [] }
        };
        this.maxDataPoints = 20;
        
        this.init();
    }
    
    init() {
        this.initSocket();
        this.loadProjects();
        this.trackVisit();
        this.loadWeather();
        this.initCharts();
        this.animateElements();
    }
    
    initSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
        });
        
        this.socket.on('system_update', (data) => {
            this.updateSystemStats(data.stats);
            this.updateServices(data.services);
            this.updateLastUpdate(data.timestamp);
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
        });
    }
    
    initCharts() {
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: {
                        color: '#334155'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                },
                y: {
                    grid: {
                        color: '#334155'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                }
            }
        };
        
        // CPU Chart
        const cpuCtx = document.getElementById('cpuChart').getContext('2d');
        this.charts.cpu = new Chart(cpuCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'CPU %',
                    data: [],
                    borderColor: '#38bdf8',
                    backgroundColor: 'rgba(56, 189, 248, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                ...chartOptions,
                scales: {
                    ...chartOptions.scales,
                    y: {
                        ...chartOptions.scales.y,
                        min: 0,
                        max: 100
                    }
                }
            }
        });
        
        // Memory Chart
        const memoryCtx = document.getElementById('memoryChart').getContext('2d');
        this.charts.memory = new Chart(memoryCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Memory %',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                ...chartOptions,
                scales: {
                    ...chartOptions.scales,
                    y: {
                        ...chartOptions.scales.y,
                        min: 0,
                        max: 100
                    }
                }
            }
        });
        
        // Network Chart
        const networkCtx = document.getElementById('networkChart').getContext('2d');
        this.charts.network = new Chart(networkCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'RX (MB/s)',
                        data: [],
                        borderColor: '#38bdf8',
                        backgroundColor: 'rgba(56, 189, 248, 0.1)',
                        fill: false,
                        tension: 0.4
                    },
                    {
                        label: 'TX (MB/s)',
                        data: [],
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        fill: false,
                        tension: 0.4
                    }
                ]
            },
            options: {
                ...chartOptions,
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            color: '#94a3b8'
                        }
                    }
                }
            }
        });
    }
    
    updateSystemStats(stats) {
        if (!stats || stats.error) return;
        
        const now = new Date().toLocaleTimeString();
        
        // Update CPU chart
        this.systemData.cpu.push(stats.cpu.percent);
        if (this.systemData.cpu.length > this.maxDataPoints) {
            this.systemData.cpu.shift();
        }
        
        this.charts.cpu.data.labels.push(now);
        if (this.charts.cpu.data.labels.length > this.maxDataPoints) {
            this.charts.cpu.data.labels.shift();
        }
        
        this.charts.cpu.data.datasets[0].data = [...this.systemData.cpu];
        this.charts.cpu.update('none');
        
        // Update Memory chart
        this.systemData.memory.push(stats.memory.percent);
        if (this.systemData.memory.length > this.maxDataPoints) {
            this.systemData.memory.shift();
        }
        
        this.charts.memory.data.labels.push(now);
        if (this.charts.memory.data.labels.length > this.maxDataPoints) {
            this.charts.memory.data.labels.shift();
        }
        
        this.charts.memory.data.datasets[0].data = [...this.systemData.memory];
        this.charts.memory.update('none');
        
        // Update Network chart
        const rxMB = stats.network.bytes_recv / (1024 * 1024);
        const txMB = stats.network.bytes_sent / (1024 * 1024);
        
        this.systemData.network.rx.push(rxMB);
        this.systemData.network.tx.push(txMB);
        
        if (this.systemData.network.rx.length > this.maxDataPoints) {
            this.systemData.network.rx.shift();
            this.systemData.network.tx.shift();
        }
        
        this.charts.network.data.labels.push(now);
        if (this.charts.network.data.labels.length > this.maxDataPoints) {
            this.charts.network.data.labels.shift();
        }
        
        this.charts.network.data.datasets[0].data = [...this.systemData.network.rx];
        this.charts.network.data.datasets[1].data = [...this.systemData.network.tx];
        this.charts.network.update('none');
        
        // Update disk usage
        if (stats.disk) {
            const diskPercent = stats.disk.percent;
            const diskUsed = this.formatBytes(stats.disk.used);
            const diskTotal = this.formatBytes(stats.disk.total);
            
            document.getElementById('disk-percent').textContent = `${diskPercent}%`;
            document.getElementById('disk-bar').style.width = `${diskPercent}%`;
            document.getElementById('disk-used').textContent = diskUsed;
            document.getElementById('disk-total').textContent = diskTotal;
        }
    }
    
    updateServices(services) {
        const servicesGrid = document.getElementById('services-grid');
        servicesGrid.innerHTML = '';
        
        if (!services || services.length === 0) {
            servicesGrid.innerHTML = `
                <div class="col-span-full text-center py-8">
                    <div class="text-4xl mb-4">🐳</div>
                    <p class="text-gray-400">No Docker services running</p>
                </div>
            `;
            return;
        }
        
        services.forEach(service => {
            const serviceCard = this.createServiceCard(service);
            servicesGrid.appendChild(serviceCard);
        });
    }
    
    createServiceCard(service) {
        const card = document.createElement('div');
        card.className = 'service-card bg-dark-card border border-dark-border rounded-2xl p-6 card-hover';
        
        const statusClass = service.status === 'running' ? 'running' : 
                           service.status === 'exited' ? 'stopped' : 'unknown';
        
        const uptime = service.uptime_seconds ? this.formatUptime(service.uptime_seconds) : 'Unknown';
        const memoryUsage = service.memory_percent ? `${service.memory_percent}%` : 'N/A';
        const cpuUsage = service.cpu_percent ? `${service.cpu_percent}%` : 'N/A';
        
        card.innerHTML = `
            <div class="flex items-center justify-between mb-4">
                <div class="flex items-center space-x-3">
                    <div class="text-2xl">🐳</div>
                    <div>
                        <h3 class="font-mono font-semibold text-white">${service.name}</h3>
                        <p class="text-sm text-gray-400">${service.image}</p>
                    </div>
                </div>
                <span class="status-badge ${statusClass}">${service.status}</span>
            </div>
            
            <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                    <span class="text-gray-400">Uptime:</span>
                    <span class="font-mono">${uptime}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">CPU:</span>
                    <span class="font-mono">${cpuUsage}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Memory:</span>
                    <span class="font-mono">${memoryUsage}</span>
                </div>
            </div>
        `;
        
        return card;
    }
    
    async loadProjects() {
        try {
            const response = await fetch('/api/projects');
            const projects = await response.json();
            
            const projectsGrid = document.getElementById('projects-grid');
            projectsGrid.innerHTML = '';
            
            projects.forEach(project => {
                const projectCard = this.createProjectCard(project);
                projectsGrid.appendChild(projectCard);
            });
        } catch (error) {
            console.error('Error loading projects:', error);
        }
    }
    
    createProjectCard(project) {
        const card = document.createElement('div');
        card.className = 'project-card bg-dark-card border border-dark-border rounded-2xl p-6 card-hover';
        
        card.innerHTML = `
            <div class="flex items-center justify-between mb-4">
                <div class="flex items-center space-x-3">
                    <div class="text-2xl">${project.icon}</div>
                    <h3 class="font-mono font-semibold text-white">${project.title}</h3>
                </div>
                <a href="${project.github}" target="_blank" class="text-neon hover:text-neon-dark transition-colors">
                    <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                    </svg>
                </a>
            </div>
            
            <p class="text-gray-400 text-sm leading-relaxed">${project.description}</p>
            
            <div class="mt-4 flex flex-wrap gap-2">
                ${project.technologies.map(tech => `
                    <span class="px-2 py-1 bg-neon/10 text-neon text-xs rounded-full border border-neon/20">
                        ${tech}
                    </span>
                `).join('')}
            </div>
        `;
        
        return card;
    }
    
    async trackVisit() {
        try {
            const response = await fetch('/api/visit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            if (data.error) {
                console.error('Error tracking visit:', data.error);
                return;
            }
            
            // Update visitor stats
            document.getElementById('total-visits').textContent = data.total_visits;
            document.getElementById('unique-visitors').textContent = data.unique_visitors;
            document.getElementById('recent-visits').textContent = data.recent_visits;
            
            if (data.last_visitor && data.last_visitor.country_name) {
                document.getElementById('last-visitor').textContent = data.last_visitor.country_name;
                document.getElementById('country-flag').textContent = this.getCountryFlag(data.last_visitor.country_code);
            }
        } catch (error) {
            console.error('Error tracking visit:', error);
        }
    }
    
    async loadWeather() {
        try {
            const response = await fetch('/api/weather');
            const data = await response.json();
            
            if (data.error) {
                document.getElementById('weather-temp').textContent = '--°C';
                document.getElementById('weather-desc').textContent = 'Unavailable';
                return;
            }
            
            document.getElementById('weather-temp').textContent = `${Math.round(data.temperature)}°C`;
            document.getElementById('weather-desc').textContent = data.description;
        } catch (error) {
            console.error('Error loading weather:', error);
        }
    }
    
    updateLastUpdate(timestamp) {
        const date = new Date(timestamp);
        document.getElementById('last-update').textContent = date.toLocaleTimeString();
    }
    
    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    formatUptime(seconds) {
        if (seconds < 60) return `${seconds}s`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
        if (seconds < 86400) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return `${hours}h ${minutes}m`;
        }
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        return `${days}d ${hours}h`;
    }
    
    getCountryFlag(countryCode) {
        const flags = {
            'TN': '🇹🇳', 'US': '🇺🇸', 'FR': '🇫🇷', 'DE': '🇩🇪', 'GB': '🇬🇧',
            'CA': '🇨🇦', 'AU': '🇦🇺', 'JP': '🇯🇵', 'CN': '🇨🇳', 'IN': '🇮🇳',
            'BR': '🇧🇷', 'RU': '🇷🇺', 'IT': '🇮🇹', 'ES': '🇪🇸', 'NL': '🇳🇱'
        };
        return flags[countryCode] || '🌍';
    }
    
    animateElements() {
        // Animate cards on load
        const cards = document.querySelectorAll('.service-card, .project-card');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.transition = 'all 0.5s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new Dashboard();
});