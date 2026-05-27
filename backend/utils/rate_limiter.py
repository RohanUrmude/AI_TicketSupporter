"""
Rate limiting configuration using Flask-Limiter.

Protects API endpoints from abuse and excessive usage:
- Global rate limit: 100 requests/minute per IP
- Ticket submission: 10 requests/minute per IP
- Analytics: 30 requests/minute per IP
"""
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

logger = logging.getLogger(__name__)

# Create limiter instance with memory storage
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],
    storage_uri="memory://",
    strategy="fixed-window"
)


def setup_rate_limiting(app):
    """Initialize rate limiter with Flask app"""
    limiter.init_app(app)
    logger.info("Rate limiting configured")
    return limiter
