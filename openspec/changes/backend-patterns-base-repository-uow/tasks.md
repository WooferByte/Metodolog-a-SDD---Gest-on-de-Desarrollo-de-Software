## 1. BaseRepository[T] Implementation

- [x] 1.1 Create `backend/infrastructure/repositories/base_repository.py`
- [x] 1.2 Implement `BaseRepository[T]` generic class with type hints
- [x] 1.3 Implement `create(entity: T) -> T` method
- [x] 1.4 Implement `get_by_id(id: int) -> Optional[T]` with soft-delete filtering
- [x] 1.5 Implement `list_all(skip: int = 0, limit: int = 100) -> list[T]` with pagination
- [x] 1.6 Implement `count() -> int` (active records only)
- [x] 1.7 Implement `update(entity: T) -> T` method
- [x] 1.8 Implement `soft_delete(id: int) -> None` (sets eliminado_en)
- [x] 1.9 Implement `hard_delete(id: int) -> None` (actual DELETE)
- [x] 1.10 Implement `execute_query(query: Select) -> list[T]` for raw queries
- [x] 1.11 Write unit tests for BaseRepository with mocked AsyncSession
- [x] 1.12 Verify type hints prevent runtime errors

## 2. Unit of Work Pattern

- [x] 2.1 Create `backend/infrastructure/uow.py`
- [x] 2.2 Implement `UnitOfWork` class with async context manager protocol
- [x] 2.3 Add repository attributes for all 14 entities (usuarios, productos, etc.)
- [x] 2.4 Implement `__aenter__` to initialize repositories
- [x] 2.5 Implement `__aexit__` with auto-commit on success
- [x] 2.6 Implement `__aexit__` with auto-rollback on exception
- [x] 2.7 Create `async def get_uow()` dependency for FastAPI
- [x] 2.8 Write unit tests for transaction atomicity
- [x] 2.9 Write integration tests with test database
- [x] 2.10 Verify rollback on IntegrityError

## 3. Authentication Dependencies

- [x] 3.1 Create `backend/infrastructure/dependencies.py`
- [x] 3.2 Implement `extract_token()` to parse Authorization header
- [x] 3.3 Implement `verify_token()` JWT validation
- [x] 3.4 Implement `get_current_user()` dependency
- [x] 3.5 Add soft-delete check in get_current_user()
- [x] 3.6 Write tests for valid/invalid token scenarios
- [x] 3.7 Write tests for 401/403 error responses
- [x] 3.8 Implement optional request-scoped caching

## 4. RBAC Factory

- [x] 4.1 Implement `require_role(roles: list[str])` factory function
- [x] 4.2 Return async callable dependency
- [x] 4.3 Validate current_user.rol.nombre against allowed roles
- [x] 4.4 Raise 403 Forbidden if role not allowed
- [x] 4.5 Write tests for single role scenarios
- [x] 4.6 Write tests for multiple roles (OR logic)
- [x] 4.7 Verify integration with FastAPI Depends()

## 5. RFC 7807 Error Middleware

- [x] 5.1 Create `backend/infrastructure/error_middleware.py`
- [x] 5.2 Implement global exception handler for Exception base class
- [x] 5.3 Format responses with RFC 7807 structure
- [x] 5.4 Map HTTP status codes to error type URIs
- [x] 5.5 Handle Pydantic validation errors with field details
- [x] 5.6 Log stack traces server-side without exposing to client
- [x] 5.7 Set `Content-Type: application/problem+json`
- [x] 5.8 Register middleware in `main.py` as exception handler
- [x] 5.9 Write tests for 400/401/403/404/500 scenarios
- [x] 5.10 Verify stack traces not exposed in responses

## 6. Integration and Documentation

- [x] 6.1 Update `main.py` to register error middleware
- [x] 6.2 Export dependencies and UoW from `__init__.py`
- [x] 6.3 Create example usage documentation
- [x] 6.4 Document BaseRepository CRUD patterns
- [x] 6.5 Document UoW transaction usage
- [x] 6.6 Document dependency injection patterns
- [x] 6.7 Update `/docs` Swagger with auth examples
- [x] 6.8 Run full integration test suite
- [x] 6.9 Verify all 15 entities work with BaseRepository
- [x] 6.10 Final verification: no breaking changes to CHANGE 3

## 7. Validation and Testing

- [x] 7.1 Run pytest with coverage > 70%
- [x] 7.2 Verify soft-delete filtering in all queries
- [x] 7.3 Verify transaction atomicity with concurrent requests
- [x] 7.4 Test role-based route protection end-to-end
- [x] 7.5 Test error response formatting with various scenarios
- [x] 7.6 Manual testing: create order with UoW (multiple repos)
- [x] 7.7 Manual testing: verify 401/403 errors on protected routes
- [x] 7.8 Verify database state after rollback
