"""
Request caching to avoid duplicate LLM processing.

Caches ticket analysis results based on ticket text hash:
- Saves API costs by avoiding redundant calls
- Improves response time for repeated requests
- TTL: 24 hours per cached entry
- Max cache size: 1000 entries
"""
import logging
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import cachetools

logger = logging.getLogger(__name__)

# TTL cache: 24 hours, max 1000 entries
_ticket_cache = cachetools.TTLCache(maxsize=1000, ttl=86400)
_analysis_cache = cachetools.TTLCache(maxsize=1000, ttl=86400)


def _hash_ticket(ticket_text: str) -> str:
    """Generate hash of ticket text for cache key"""
    return hashlib.sha256(ticket_text.encode()).hexdigest()[:16]


def get_cached_ticket_result(ticket_text: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve cached ticket processing result if available.

    Args:
        ticket_text: The ticket text to look up

    Returns:
        Cached result dict or None if not found/expired
    """
    key = _hash_ticket(ticket_text)
    if key in _ticket_cache:
        logger.info(f"Cache HIT for ticket (key={key})")
        return _ticket_cache[key]
    logger.debug(f"Cache MISS for ticket (key={key})")
    return None


def cache_ticket_result(ticket_text: str, result: Dict[str, Any]) -> None:
    """
    Store ticket processing result in cache.

    Args:
        ticket_text: The original ticket text
        result: The processing result to cache
    """
    key = _hash_ticket(ticket_text)
    _ticket_cache[key] = result
    logger.info(f"Cached ticket result (key={key}, ttl=24h)")


def get_cached_analysis(ticket_text: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve cached ticket analysis if available.

    Args:
        ticket_text: The ticket text to analyze

    Returns:
        Cached analysis dict or None if not found/expired
    """
    key = _hash_ticket(ticket_text)
    if key in _analysis_cache:
        logger.info(f"Cache HIT for analysis (key={key})")
        return _analysis_cache[key]
    logger.debug(f"Cache MISS for analysis (key={key})")
    return None


def cache_analysis(ticket_text: str, analysis: Dict[str, Any]) -> None:
    """
    Store ticket analysis in cache.

    Args:
        ticket_text: The original ticket text
        analysis: The analysis result to cache
    """
    key = _hash_ticket(ticket_text)
    _analysis_cache[key] = analysis
    logger.info(f"Cached analysis (key={key}, ttl=24h)")


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics for monitoring"""
    return {
        "ticket_cache": {
            "size": len(_ticket_cache),
            "maxsize": _ticket_cache.maxsize,
            "ttl_seconds": _ticket_cache.ttl
        },
        "analysis_cache": {
            "size": len(_analysis_cache),
            "maxsize": _analysis_cache.maxsize,
            "ttl_seconds": _analysis_cache.ttl
        }
    }


def clear_caches() -> None:
    """Clear all caches (for testing/maintenance)"""
    _ticket_cache.clear()
    _analysis_cache.clear()
    logger.info("All caches cleared")
