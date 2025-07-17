import docker
from datetime import datetime, timedelta
import json

class DockerMonitor:
    """Monitor Docker containers and services"""
    
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.docker_available = True
        except Exception as e:
            print(f"Docker not available: {e}")
            self.docker_available = False
    
    def get_running_containers(self):
        """Get list of running Docker containers"""
        if not self.docker_available:
            return []
        
        try:
            containers = self.client.containers.list()
            container_info = []
            
            for container in containers:
                try:
                    # Get container stats
                    stats = container.stats(stream=False)
                    
                    # Calculate CPU usage
                    cpu_percent = self._calculate_cpu_percent(stats)
                    
                    # Calculate memory usage
                    memory_usage = stats['memory_stats'].get('usage', 0)
                    memory_limit = stats['memory_stats'].get('limit', 0)
                    memory_percent = (memory_usage / memory_limit * 100) if memory_limit > 0 else 0
                    
                    # Get container creation time
                    created = datetime.fromisoformat(container.attrs['Created'].replace('Z', '+00:00'))
                    uptime = datetime.now() - created.replace(tzinfo=None)
                    
                    container_info.append({
                        'id': container.id[:12],
                        'name': container.name,
                        'image': container.image.tags[0] if container.image.tags else 'unknown',
                        'status': container.status,
                        'state': container.attrs['State']['Status'],
                        'created': created.isoformat(),
                        'uptime_seconds': int(uptime.total_seconds()),
                        'ports': self._format_ports(container.ports),
                        'cpu_percent': round(cpu_percent, 1),
                        'memory_percent': round(memory_percent, 1),
                        'memory_usage': memory_usage,
                        'network_rx': self._get_network_stat(stats, 'rx_bytes'),
                        'network_tx': self._get_network_stat(stats, 'tx_bytes')
                    })
                except Exception as e:
                    # If we can't get stats, just add basic info
                    container_info.append({
                        'id': container.id[:12],
                        'name': container.name,
                        'image': container.image.tags[0] if container.image.tags else 'unknown',
                        'status': container.status,
                        'state': container.attrs['State']['Status'],
                        'error': str(e)
                    })
            
            return container_info
        except Exception as e:
            print(f"Error getting containers: {e}")
            return []
    
    def _calculate_cpu_percent(self, stats):
        """Calculate CPU usage percentage"""
        try:
            cpu_stats = stats['cpu_stats']
            precpu_stats = stats['precpu_stats']
            
            cpu_usage = cpu_stats['cpu_usage']['total_usage']
            precpu_usage = precpu_stats['cpu_usage']['total_usage']
            
            system_usage = cpu_stats['system_cpu_usage']
            presystem_usage = precpu_stats['system_cpu_usage']
            
            cpu_num = len(cpu_stats['cpu_usage']['percpu_usage'])
            
            cpu_delta = cpu_usage - precpu_usage
            system_delta = system_usage - presystem_usage
            
            if system_delta > 0 and cpu_delta > 0:
                return (cpu_delta / system_delta) * cpu_num * 100
            return 0
        except (KeyError, ZeroDivisionError):
            return 0
    
    def _get_network_stat(self, stats, stat_name):
        """Get network statistics"""
        try:
            networks = stats['networks']
            total = 0
            for interface in networks.values():
                total += interface.get(stat_name, 0)
            return total
        except KeyError:
            return 0
    
    def _format_ports(self, ports):
        """Format port mappings"""
        if not ports:
            return []
        
        formatted_ports = []
        for container_port, host_bindings in ports.items():
            if host_bindings:
                for binding in host_bindings:
                    formatted_ports.append({
                        'container_port': container_port,
                        'host_port': binding['HostPort'],
                        'host_ip': binding['HostIp']
                    })
        return formatted_ports
    
    def get_docker_info(self):
        """Get Docker system information"""
        if not self.docker_available:
            return {'error': 'Docker not available'}
        
        try:
            info = self.client.info()
            version = self.client.version()
            
            return {
                'version': version['Version'],
                'api_version': version['ApiVersion'],
                'containers': info['Containers'],
                'containers_running': info['ContainersRunning'],
                'containers_paused': info['ContainersPaused'],
                'containers_stopped': info['ContainersStopped'],
                'images': info['Images'],
                'server_version': info['ServerVersion'],
                'storage_driver': info['Driver'],
                'total_memory': info['MemTotal'],
                'ncpu': info['NCPU']
            }
        except Exception as e:
            return {'error': str(e)}
    
    def format_uptime(self, seconds):
        """Format uptime in human readable format"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days}d {hours}h"