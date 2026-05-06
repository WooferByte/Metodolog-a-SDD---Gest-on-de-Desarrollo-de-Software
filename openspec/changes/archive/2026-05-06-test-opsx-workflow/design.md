## Overview

Feature flag system to validate OPSX workflow end-to-end. Minimal design to test artifact generation and implementation.

## Architecture

```
Feature Flags Flow:
1. Backend: Redis-backed feature flags service (FastAPI)
2. Frontend: React hook to consume feature flags
3. CLI: Simple get/set commands for flag management
```

## Implementation Strategy

### Phase 1: Backend Service
- Create `backend/features/flags.py` with FeatureFlagService
- Add Redis integration (if available) or in-memory fallback
- Expose FastAPI endpoints: `GET /api/flags`, `POST /api/flags/{name}`

### Phase 2: Frontend Hook
- Create `frontend/src/hooks/useFeatureFlag.ts`
- Hook fetches flags from backend on mount
- Provides `isEnabled(flagName)` utility

### Phase 3: Documentation
- Add flag management guide to docs
- Example: enabling/disabling features for testing

## Database Schema

No schema changes — feature flags stored in-memory or Redis.

## API Endpoints

- `GET /api/flags` — List all flags
- `GET /api/flags/{name}` — Get flag status
- `POST /api/flags/{name}` — Set flag status (admin only)

## Testing Strategy

- Unit tests for FeatureFlagService
- Integration test: POST flag → verify GET reflects change
- Frontend test: Hook renders correctly based on flag state
