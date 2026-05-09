"""
Shared slowapi rate limiter instance.

Defined here (not in main.py) to avoid circular imports when routers
import the limiter instance for @limiter.limit() decorators.

Usage in routers:
    from core.limiter import limiter

Usage in main.py:
    from core.limiter import limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, ...)
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
