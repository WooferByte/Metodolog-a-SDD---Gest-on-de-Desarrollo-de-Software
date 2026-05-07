## ADDED Requirements

### Requirement: AuthStore manages JWT tokens and user session

The authStore SHALL provide centralized state for user authentication including access token, refresh token, authenticated user data, and authentication status.

#### Scenario: Initial state before login
- **WHEN** application first loads
- **THEN** authStore contains null user, empty tokens, and isAuthenticated = false

#### Scenario: Store tokens after login
- **WHEN** user logs in successfully
- **THEN** authStore saves accessToken, refreshToken, and user object in state

#### Scenario: Check authentication status
- **WHEN** component queries isAuthenticated selector
- **THEN** returns true if accessToken and user exist, false otherwise

#### Scenario: Retrieve user data with role
- **WHEN** component calls getUser() action
- **THEN** returns current authenticated user with roles array

### Requirement: AuthStore has role-based helper methods

The authStore SHALL provide a hasRole() helper method to check if the current user has a specific role.

#### Scenario: Check if user has admin role
- **WHEN** component calls authStore.hasRole('ADMIN')
- **THEN** returns true if user has ADMIN role, false otherwise

#### Scenario: Check multiple roles
- **WHEN** component calls authStore.hasRole('STOCK') on a STOCK user
- **THEN** returns true

### Requirement: AuthStore handles token updates

The authStore SHALL provide updateTokens() action to refresh JWT tokens when they expire.

#### Scenario: Update tokens after refresh endpoint
- **WHEN** frontend calls authStore.updateTokens(newAccessToken, newRefreshToken)
- **THEN** authStore updates both tokens in state

#### Scenario: Access token persisted, refresh token not persisted
- **WHEN** page reloads
- **THEN** accessToken is restored from localStorage, but refreshToken is reset to empty (security)

### Requirement: AuthStore has logout action

The authStore SHALL provide logout() action to clear all authentication data.

#### Scenario: Clear state on logout
- **WHEN** user calls authStore.logout()
- **THEN** all tokens, user data cleared; isAuthenticated becomes false

#### Scenario: Remove persisted token
- **WHEN** user logs out
- **THEN** accessToken removed from localStorage

