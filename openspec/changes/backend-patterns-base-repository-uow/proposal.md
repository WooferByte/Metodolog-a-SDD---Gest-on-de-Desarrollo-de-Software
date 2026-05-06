## Why

CHANGE 3 created the database foundation with SQLModel entities. Now we need the **infrastructure layer** to decouple repositories from business logic and implement Unit of Work pattern for atomic transactions. This enables clean, testable service layer code and ensures all subsequent CHANGEs (auth, products, orders) have a solid foundation.

## What Changes

- Create `BaseRepository[T]` generic with DDD patterns (Entity, ID, aggregate query methods)
- Implement `UnitOfWork` async context manager for coordinating multiple repositories in a single transaction
- Create `get_current_user()` dependency for JWT verification
- Create `require_role()` factory for role-based access control
- Implement RFC 7807 error middleware for standardized error responses

## Capabilities

### New Capabilities
- `base-repository-pattern`: Generic repository interface with soft-delete support
- `unit-of-work-pattern`: Async UoW context manager for transaction coordination
- `authentication-dependencies`: FastAPI dependencies for JWT extraction and validation
- `rbac-factory`: Factory for role-based route protection
- `error-handling-rfc7807`: RFC 7807 compliant error responses

### Modified Capabilities
<!-- None for this change -->

## Impact

- **Backend Infrastructure**: All subsequent auth/product/order endpoints will depend on these patterns
- **DDD Compliance**: Ensures repository layer is decoupled from domain entities (CHANGE 3 models)
- **Transaction Safety**: UoW guarantees atomicity across multiple repository operations
- **Security**: JWT extraction and role validation centralized for all future endpoints
- **Error Handling**: Standardized error format reduces bugs and improves client experience
