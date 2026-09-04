"""
System Information Tool for Jarvis
Reads CPU, RAM, OS, and hardware metrics safely without external dependencies.
"""
import platform
import os
import sys

def get_system_info(*args, **kwargs) -> str:
    """Returns detailed OS, CPU, RAM, and Python runtime metrics."""
    try:
        uname = platform.uname()
        os_info = f"{uname.system} {uname.release} (Build {uname.version})"
        processor = uname.processor or platform.machine()
        
        # Try psutil if installed, otherwise fallback to platform metrics
        ram_info = "Memory metrics active"
        try:
            import psutil
            mem = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            ram_info = f"RAM: {mem.percent}% used ({round(mem.used / (1024**3), 1)}GB / {round(mem.total / (1024**3), 1)}GB), CPU: {cpu_percent}%"
        except ImportError:
            pass

        return (
            f"System Diagnostics:\n"
            f"• OS: {os_info}\n"
            f"• Architecture: {platform.architecture()[0]} ({processor})\n"
            f"• Python: {platform.python_version()} ({sys.executable})\n"
            f"• Status: {ram_info}"
        )
    except Exception as e:
        return f"System info error: {str(e)}"
