## Why

Frontend React requires centralized state management for authentication (tokens, user data, roles), shopping cart (items, totals), payment workflow (checkout steps, status), and UI state (theme, sidebar, notifications). Without this, state management becomes fragmented across components, leading to prop drilling, inconsistent state, and difficult debugging. Zustand provides a minimal, type-safe, and performant solution that integrates seamlessly with the React frontend.

## What Changes

- **authStore**: Central authentication state with login/logout/updateTokens actions, JWT token management, and role-based helper methods
- **cartStore**: Shopping cart state with item management (add/remove/update quantity), computed selectors (totalItems, totalPrice), and localStorage persistence
- **paymentStore**: Payment workflow state for multi-step checkout (step tracking, preference ID, payment status)
- **uiStore**: UI state for theme (light/dark), sidebar toggle, and toast notifications with selective localStorage persistence

## Capabilities

### New Capabilities

- `zustand-auth-store`: User authentication state with JWT token persistence, role checking, and session management
- `zustand-cart-store`: Shopping cart state with item persistence in localStorage, calculations, and personalization
- `zustand-payment-store`: Payment checkout workflow state for multi-step payment process
- `zustand-ui-store`: Application-wide UI state (theme preference, navigation state, notifications)

### Modified Capabilities

(None - this is a new foundational feature)

## Impact

- **Frontend code**: All React components can now access auth, cart, payment, and UI state without prop drilling
- **Dependencies**: Adds `zustand@5.0.8` to package.json
- **localStorage**: Cart items and UI theme are persisted across browser sessions
- **TypeScript**: Full type safety across all stores via Zustand's TypeScript support
- **Future features**: Payment checkout UI (US-045), orders UI, admin dashboard all depend on this foundation

