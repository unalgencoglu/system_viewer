"""
Çalışılan işletim sistemine göre doğru toplayıcıyı seçer.
Flask tarafı sadece `from collector import get_processes` gibi kullanır.
"""
import platform

if platform.system() == "Linux":
    from .linux import get_system_info, get_system_stats, get_processes, get_process_detail, control_process
else:
    from .windows import get_system_info, get_system_stats, get_processes, get_process_detail, control_process

__all__ = ["get_system_info", "get_system_stats", "get_processes", "get_process_detail", "control_process"]
