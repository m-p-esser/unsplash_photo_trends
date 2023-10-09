"""Random Utility functions """

import functools
import time

import psutil
from dotenv import dotenv_values


def timer(func):
    """Track time of a function"""

    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        """Track time"""
        start_time = time.perf_counter()
        value = func(*args, **kwargs)
        end_time = time.perf_counter()
        duration = end_time - start_time
        print(f"Function {func.__name__!r} took {duration:.4f} seconds to complete.")
        return value

    return wrapper_timer


def load_env_variables() -> dict:
    """Load Environment variables into memory"""
    environment = dotenv_values("make/.env")

    env_variables = dotenv_values(
        f"make/base.env"
    )  # used across enviroments (dev, test, prod)
    env_variables.update(environment)  # Combine both

    return env_variables


def check_system_utilization():
    """Analyze CPU and Memory Usage"""
    vmem = psutil.virtual_memory()
    system_utilization = {
        "cpu_num": psutil.cpu_count(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_full_info": {
            "vmem_available_mb": vmem.available / (1024**2),
            "vmem_total_mb": vmem.total / (1024**2),
            "vmem_percent": vmem.percent,
        },
    }
    return system_utilization
