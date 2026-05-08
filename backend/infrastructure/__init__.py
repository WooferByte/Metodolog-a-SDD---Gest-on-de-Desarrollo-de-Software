"""
Infrastructure layer for DDD pattern.

Exports:
- BaseRepository: Generic repository for all entities
- UnitOfWork: Transaction coordinator
- Dependencies: FastAPI dependency injection functions
- Error middleware: RFC 7807 error handling
"""
from .repositories.base_repository import BaseRepository
from .uow import UnitOfWork, get_uow
from .dependencies import (
    get_current_user,
    require_role,
    extract_token,
    verify_token_dependency,
)
from .error_middleware import register_error_handlers

__all__ = [
    "BaseRepository",
    "UnitOfWork",
    "get_uow",
    "get_current_user",
    "require_role",
    "extract_token",
    "verify_token_dependency",
    "register_error_handlers",
]
