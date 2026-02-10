import pybreaker
import logging
from typing import Optional, Dict, Any

# Configure Logger
logger = logging.getLogger("circuit_breaker")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Custom Exceptions
class APIRateLimitError(Exception):
    """Raised when external API returns 429."""
    pass

class APIError(Exception):
    """Raised when external API returns 5xx."""
    pass

# Circuit Breaker Listener for Logging
class LogListener(pybreaker.CircuitBreakerListener):
    def state_change(self, cb, old_state, new_state):
        if new_state == pybreaker.STATE_OPEN:
            logger.warning(f"Circuit {cb.name} OPENED - Service degraded")
        elif new_state == pybreaker.STATE_CLOSED:
            logger.info(f"Circuit {cb.name} CLOSED - Service recovered")

# Circuit Configurations
redis_circuit = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    listeners=[LogListener()]
)
redis_circuit.name = "Redis"

# Mock Redis Client (Replace with real client in production)
class MockRedis:
    def get(self, key):
        # Allow injecting failures for testing
        return None

    def setex(self, key, ttl, value):
        pass

redis_client = MockRedis()

@redis_circuit
def fetch_from_redis(key: str) -> Optional[str]:
    """
    Wraps Redis GET with circuit breaker.
    Opens circuit after 5 consecutive failures.
    """
    try:
        return redis_client.get(key)
    except Exception as e:
        logger.error(f"Redis fetch failed: {e}")
        raise e

def call_external_pnr_api(pnr: str) -> Dict[str, Any]:
    """
    Mock function to simulate external PNR API call.
    In real implementation, this would use httpx.
    """
    # Simulate success or failure based on test config
    # For now, just return a dummy response
    return {"pnr": pnr, "status": "CNF", "source": "API"}

def get_pnr_status(pnr: str) -> Dict[str, Any]:
    """
    Fetch PNR status with fallback chain: Redis -> API -> Graceful Error.
    """
    # L1: Redis Cache
    try:
        cached_data = fetch_from_redis(f"pnr:{pnr}")
        if cached_data:
            return {"pnr": pnr, "status": "CNF", "source": "CACHE"} # Mock parsing
    except pybreaker.CircuitBreakerError:
        logger.warning("Redis circuit open - failing over to API")
    except Exception:
        pass # Logged in fetch_from_redis

    # L2: External API
    try:
        result = call_external_pnr_api(pnr)
        # Try to cache result (ignore failures)
        try:
            redis_client.setex(f"pnr:{pnr}", 900, "dummy_json")
        except:
            pass
        return result
    except APIRateLimitError:
        logger.error("PNR API rate limit exceeded")
        return {
            "status": "unavailable",
            "message": "Service temporarily degraded. Please try again later."
        }
    except Exception as e:
        logger.error(f"PNR API failed: {e}")
        return {
            "status": "unavailable",
            "message": "Service temporarily degraded. Please try again later."
        }
