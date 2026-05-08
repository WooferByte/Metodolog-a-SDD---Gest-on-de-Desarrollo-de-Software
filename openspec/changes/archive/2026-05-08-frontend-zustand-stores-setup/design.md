## Context

The frontend currently uses React with Vite, TypeScript, and TanStack Query for server state. We need client state management for:
- **Authentication**: JWT tokens, user data, session state
- **Shopping cart**: Items, quantities, totals, personalization
- **Checkout workflow**: Multi-step payment process state
- **UI preferences**: Theme, sidebar visibility, notifications

Current state: No centralized client state management exists. Components currently don't have shared state layer.

Zustand provides a minimal, type-safe alternative to Redux/Context API:
- Single hook API (`useStore()`)
- No boilerplate (no providers, reducers, etc.)
- Fine-grained subscriptions (components only re-render when selected state changes)
- Selective persistence (localStorage for auth token, cart; nothing for payment)
- Excellent TypeScript support

## Goals / Non-Goals

**Goals:**
- Implement 4 Zustand stores with proper TypeScript types
- Auth store with JWT token management and role helpers
- Cart store with persistence and personalization support
- Payment store for checkout workflow (no persistence for security)
- UI store with theme and sidebar state
- Selective localStorage persistence (auth accessToken, cart items, ui theme)
- Foundation for downstream features (payment UI, orders UI, admin dashboard)

**Non-Goals:**
- Complex state mutations (no Immer middleware needed at this stage)
- Redux DevTools integration (can add later if needed)
- Server state management (TanStack Query handles that)
- Global error handling (that's in error middleware)

## Decisions

### Decision 1: Choose Zustand over Redux / Context API

**Rationale**: Zustand provides the simplest, most performant solution for this use case.

**Alternatives considered:**
- Redux: Overkill for 4 simple stores, too much boilerplate
- Context API: Prop drilling, complex with multiple contexts, doesn't prevent unnecessary re-renders
- MobX: Similar to Zustand but heavier, less TypeScript-friendly

**Choice**: Zustand v5.0.8
- Minimal API (just `create()`)
- Fine-grained subscriptions (select only what you need)
- TypeScript-first with excellent inference
- Selective middleware support (persist only where needed)

### Decision 2: Four separate stores, not one monolithic store

**Rationale**: Separation of concerns, easier to test, easier to add/remove middleware per store.

**Alternatives considered:**
- Single combined store with all state: Couples unrelated features, harder to test
- Separate stores: Better modularity, cleaner structure

**Choice**: Four stores (auth, cart, payment, ui) + export hook factory for combined access if needed

### Decision 3: Selective localStorage persistence

**Rationale**: Different state has different persistence needs and security implications.

**Auth Store:**
- Persist: `accessToken` only (frontend can re-login if needed)
- Don't persist: `refreshToken` (security: never store refresh token in localStorage if possible)
- Implication: User stays logged in across sessions (UX) but safe (refresh token not exposed)

**Cart Store:**
- Persist: All items with quantities and personalization
- Reason: Users expect cart to survive page reload, tab close, logout/login

**Payment Store:**
- Persist: NOTHING (zero persistence)
- Reason: Security critical - payment state must never persist across page reloads
- Implication: If user reloads mid-checkout, they restart from step 1 (acceptable UX trade-off)

**UI Store:**
- Persist: Theme preference only
- Don't persist: Sidebar (resets on reload), Toasts (ephemeral)

### Decision 4: Use TypeScript `create<T>()()` pattern for type safety

**Rationale**: Full type inference requires double parentheses for middleware compatibility.

```typescript
// ✅ Correct for TypeScript + middleware
const useAuthStore = create<AuthStore>()((set) => ({ ... }))

// ❌ Wrong - breaks type inference
const useAuthStore = create<AuthStore>((set) => ({ ... })
```

### Decision 5: Slice pattern for organization

**Rationale**: Each store exports as separate file for clarity and future slices if needed.

```
frontend/src/store/
├── authStore.ts        (auth slice)
├── cartStore.ts        (cart slice)
├── paymentStore.ts     (payment slice)
├── uiStore.ts          (ui slice)
└── index.ts            (re-exports)
```

## Risks / Trade-offs

### Risk: localStorage accessible to XSS attacks

**Mitigation**: 
- Store only accessToken (not refreshToken) in localStorage
- Implement Content Security Policy (CSP) to prevent XSS
- Use httpOnly cookies for refreshToken if backend supports it (future improvement)

### Risk: Cart persistence survives logout, which could be unexpected

**Mitigation**: 
- This is acceptable UX (cart is not sensitive data)
- If needed, cart can be cleared manually on logout (not automatic)
- Frontend can provide "Clear Cart" button

### Risk: Payment state reset on reload loses checkout progress

**Mitigation**: 
- This is acceptable for security (prevents payment hijacking)
- UX: Show "Your checkout session expired, please start over" if refresh happens mid-payment
- Acceptable trade-off: Security > convenience for payments

### Risk: Multiple tabs can cause state sync issues

**Mitigation**: 
- Zustand automatically syncs state across tabs with localStorage
- localStorage change events trigger store updates
- Test with multiple tabs during implementation

### Risk: Complex derived state might cause performance issues

**Mitigation**: 
- Computed selectors (totalItems, totalPrice) are calculated on each selector call (minimal)
- No memoization needed for simple calculations
- If performance issue arises: use Reselect library or `useShallow` selector

## Migration Plan

**Phase 1: Setup (Task 1-3)**
- Install Zustand
- Create store files with proper TypeScript types
- Export hooks from `src/store/index.ts`

**Phase 2: Integration (Task 4-6)**
- Integrate authStore with Axios JWT interceptor (separate change)
- Integrate cartStore with Cart UI components (separate change)
- Test persistence in localStorage

**Phase 3: Testing (Task 7-8)**
- Unit tests for each store
- localStorage persistence tests
- Multi-tab synchronization tests

**Rollback Strategy:**
- If critical issue: revert commit
- No database migrations, no backwards compatibility issues

## Open Questions

1. Should we add `useShallow` selector util to prevent re-renders with multiple selections? (Minor optimization)
2. Should auth store also track `lastLoginTime` for UI? (Deferred to next change)
3. Should payment store validate state transitions (e.g., prevent going from step 3 → 1)? (Deferred to checkout UI change)

