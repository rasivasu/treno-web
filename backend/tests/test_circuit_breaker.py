import pytest
import pybreaker
from app.services.circuit_breaker import (
    redis_circuit, 
    fetch_from_redis, 
    get_pnr_status, 
    redis_client,
    APIRateLimitError, 
    APIError,
    logger
)
from unittest.mock import patch, MagicMock

# Reset circuit before tests
@pytest.fixture(autouse=True)
def reset_circuit():
    redis_circuit.close()
    yield
    redis_circuit.close()

def test_circuit_opens_after_failures():
    # Mock Redis to fail
    with patch.object(redis_client, 'get', side_effect=Exception("Redis Down")):
        # Fail 5 times (fail_max)
        for _ in range(5):
            try:
                fetch_from_redis("key")
            except Exception:
                pass
        
        # 6th time should raise CircuitBreakerError immediately
        with pytest.raises(pybreaker.CircuitBreakerError):
            fetch_from_redis("key")
            
        assert redis_circuit.current_state == pybreaker.STATE_OPEN

def test_fallback_to_api_when_circuit_open():
    # Force open circuit
    redis_circuit.open()
    
    with patch('app.services.circuit_breaker.call_external_pnr_api') as mock_api:
        mock_api.return_value = {"status": "SUCCESS", "source": "API"}
        
        result = get_pnr_status("12345")
        
        assert result["source"] == "API"
        mock_api.assert_called_once()

def test_graceful_error_on_api_failure():
    # Force open circuit (so it skips Redis)
    redis_circuit.open()
    
    with patch('app.services.circuit_breaker.call_external_pnr_api', side_effect=Exception("API Down")):
        result = get_pnr_status("12345")
        
        assert result["status"] == "unavailable"
        assert "Service temporarily degraded" in result["message"]

def test_graceful_error_on_rate_limit():
    redis_circuit.open()
    
    with patch('app.services.circuit_breaker.call_external_pnr_api', side_effect=APIRateLimitError("429")):
        result = get_pnr_status("12345")
        
        assert result["status"] == "unavailable" 
