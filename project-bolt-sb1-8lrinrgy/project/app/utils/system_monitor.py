import psutil
import platform
from datetime import datetime

class SystemMonitor:
    """Monitor system statistics using psutil"""
    
    def __init__(self):
        self.boot_time = datetime.fromtimestamp(psutil.boot_time())
    
    def get_system_stats(self):
        """Get comprehensive system statistics"""
        try:
            # CPU information
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory information
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk information
            disk = psutil.disk_usage('/')
            
            # Network information
            net_io = psutil.net_io_counters()
            
            # System information
            uptime = datetime.now() - self.boot_time
            
            return {
                'cpu': {
                    'percent': round(cpu_percent, 1),
                    'count': cpu_count,
                    'frequency': round(cpu_freq.current, 2) if cpu_freq else 0
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': round(memory.percent, 1),
                    'used': memory.used
                },
                'swap': {
                    'total': swap.total,
                    'used': swap.used,
                    'percent': round(swap.percent, 1)
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': round((disk.used / disk.total) * 100, 1)
                },
                'network': {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv
                },
                'system': {
                    'platform': platform.system(),
                    'platform_version': platform.version(),
                    'architecture': platform.machine(),
                    'hostname': platform.node(),
                    'uptime_seconds': int(uptime.total_seconds())
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_process_info(self, limit=10):
        """Get top processes by CPU usage"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    if proc_info['cpu_percent'] > 0:
                        processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage and return top processes
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            return processes[:limit]
        except Exception as e:
            return []
    
    def format_bytes(self, bytes_value):
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"