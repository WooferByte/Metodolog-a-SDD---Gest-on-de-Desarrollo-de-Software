## ADDED Requirements

### Requirement: PaymentStore manages checkout workflow state

The paymentStore SHALL track the current step in the multi-step checkout process (cart review, address selection, payment method, confirmation).

#### Scenario: Initial checkout state
- **WHEN** user enters checkout flow
- **THEN** checkoutStep is 1, preferenceId is null, paymentStatus is pending

#### Scenario: Advance checkout steps
- **WHEN** user calls paymentStore.startCheckout()
- **THEN** checkoutStep is set to 1 (cart review)

#### Scenario: Update checkout step
- **WHEN** user clicks "Continue to address"
- **THEN** checkoutStep is incremented to next step

### Requirement: PaymentStore tracks payment preference

The paymentStore SHALL store MercadoPago preferenceId for the current payment attempt.

#### Scenario: Set preference ID
- **WHEN** checkout service creates MercadoPago preference
- **THEN** paymentStore.setPreference(preferenceId) stores the ID

#### Scenario: Retrieve preference ID
- **WHEN** checkout UI needs to redirect to payment
- **THEN** paymentStore.getPreferenceId() returns current preferenceId

### Requirement: PaymentStore tracks payment status

The paymentStore SHALL maintain payment processing status (pending, processing, approved, rejected).

#### Scenario: Start payment processing
- **WHEN** user submits payment
- **THEN** paymentStore.updatePaymentStatus('processing')

#### Scenario: Handle approved payment
- **WHEN** webhook confirms payment approved
- **THEN** paymentStore.updatePaymentStatus('approved')

#### Scenario: Handle rejected payment
- **WHEN** webhook indicates payment failed
- **THEN** paymentStore.updatePaymentStatus('rejected')

### Requirement: PaymentStore resets after checkout complete

The paymentStore SHALL provide resetPayment() to clear workflow state after successful order creation.

#### Scenario: Reset payment state
- **WHEN** order created successfully
- **THEN** paymentStore.resetPayment() clears checkoutStep, preferenceId, paymentStatus

#### Scenario: No persistence on reset
- **WHEN** page reloads
- **THEN** payment state does NOT persist (no localStorage)

### Requirement: PaymentStore does NOT persist to localStorage

The paymentStore SHALL NOT use localStorage persistence - payment state resets on page reload for security.

#### Scenario: Payment state lost on reload
- **WHEN** user is in middle of checkout and page reloads
- **THEN** checkout state is completely reset (required for security)

