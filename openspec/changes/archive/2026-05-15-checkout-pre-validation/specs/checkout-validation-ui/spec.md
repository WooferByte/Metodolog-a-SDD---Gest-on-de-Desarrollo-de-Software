## ADDED Requirements

### Requirement: Checkout page fires validation on entry

The checkout page SHALL call `POST /api/v1/pedidos/validar` automatically when the user enters the checkout route, before rendering any order form fields. The request payload is assembled from the current Zustand cartStore state.

#### Scenario: Validation fires on checkout route mount

- **WHEN** the user navigates to `/checkout`
- **THEN** `useCheckoutValidation` mutation is invoked with the current cart items and selected address ID
- **THEN** a loading indicator is shown while the request is in flight

#### Scenario: Validation succeeds — checkout proceeds

- **WHEN** the validation response has all arrays empty and all flags false
- **THEN** the checkout form is displayed without any modal or alert

#### Scenario: Validation fails with hard errors

- **WHEN** `carritoVacio=true` OR `sinDireccion=true` in the response (HTTP 422)
- **THEN** a blocking modal is shown that prevents proceeding and directs the user to fix the issue (return to cart or add an address)

#### Scenario: Validation returns soft warnings

- **WHEN** `stockInsuficiente` or `cambiosDePrecio` arrays are non-empty (HTTP 200)
- **THEN** a non-blocking modal is shown listing each issue with product name and detail
- **THEN** the user can dismiss/confirm to proceed despite the warnings, or cancel to return to cart

#### Scenario: Validation returns invalid products

- **WHEN** `productosInvalidos` array is non-empty
- **THEN** the modal lists the unavailable products and prompts the user to remove them from the cart before proceeding (cannot proceed with invalid products)

### Requirement: useCheckoutValidation hook encapsulates validation API call

The `useCheckoutValidation` hook SHALL use `useMutation` from TanStack Query v5 to call the validation endpoint. It SHALL NOT use `useQuery` or `useEffect + fetch`.

#### Scenario: Hook triggers mutation imperatively

- **WHEN** the checkout page mounts
- **THEN** `mutation.mutate(payload)` is called once with the assembled cart payload
- **THEN** subsequent re-renders do NOT re-trigger the mutation

#### Scenario: Hook exposes loading state

- **WHEN** the mutation is pending
- **THEN** `mutation.isPending` is `true` and the calling component shows a loading indicator

#### Scenario: Hook exposes validation result

- **WHEN** the mutation succeeds
- **THEN** `mutation.data` contains the `ValidarCarritoResponse` object

#### Scenario: Hook handles network error

- **WHEN** the API call fails with a network error or non-2xx status
- **THEN** `mutation.isError` is `true` and an error toast is shown via the global toast system

### Requirement: CheckoutValidationModal renders issues clearly

The `CheckoutValidationModal` component SHALL display validation issues in a readable format with appropriate severity distinction between hard blocks and soft warnings.

#### Scenario: Stock shortage displayed with product name and numbers

- **WHEN** modal renders a stock shortage issue
- **THEN** it shows the product name, current stock, and requested quantity in a human-readable sentence

#### Scenario: Price change displayed with before/after values

- **WHEN** modal renders a price change
- **THEN** it shows the product name, the cart price (old), and the current price (new) formatted as currency

#### Scenario: Hard-block modal has no "proceed" option

- **WHEN** modal is shown for `carritoVacio` or `sinDireccion`
- **THEN** only a "Go back" / "Return to cart" action button is present — no confirm/proceed button

#### Scenario: Soft-warning modal has both confirm and cancel

- **WHEN** modal is shown for stock or price issues only
- **THEN** both "Proceed anyway" and "Return to cart" buttons are present
- **THEN** clicking "Proceed anyway" closes the modal and shows the checkout form

### Requirement: Validation UI follows FSD structure

Frontend code for checkout validation SHALL live under `frontend/src/features/checkout/` and SHALL NOT import from sibling features (e.g., `features/products`).

#### Scenario: Feature directory contains hook, component, and types

- **WHEN** the `features/checkout` directory is created
- **THEN** it contains `hooks/useCheckoutValidation.ts`, `components/CheckoutValidationModal.tsx`, and `types/index.ts`
- **THEN** all imports within the feature use the `@/` path alias
