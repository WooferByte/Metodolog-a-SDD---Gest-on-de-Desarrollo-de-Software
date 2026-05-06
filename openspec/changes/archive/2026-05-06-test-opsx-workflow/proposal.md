## Why

Testing that the OPSX workflow (propose → design → apply → archive) executes end-to-end without errors. Validates CLI integration and artifact lifecycle.

## What Changes

- Create a minimal feature flag capability to test spec → design → tasks → implementation → archive flow
- Verify all CLI commands work correctly
- Confirm artifacts sync properly to main specs

## Capabilities

### New Capabilities
- `feature-flags`: Basic feature flag system for toggling functionality at runtime

### Modified Capabilities
<!-- None for this test -->

## Impact

- Tests: OPSX workflow validation
- Scope: Test-only, no production impact
