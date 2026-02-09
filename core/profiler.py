import time
import functools
import logging

# Configure basic logging if not already done
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProfileTimer:
    def __init__(self, name="Timer"):
        self.name = name
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.perf_counter()
        duration = end_time - self.start_time
        logger.info(f"[PROFILE] {self.name} took {duration:.4f} seconds")

def profile(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        duration = end_time - start_time
        logger.info(f"[PROFILE] Function '{func.__name__}' took {duration:.4f} seconds")
        return result
    return wrapper
