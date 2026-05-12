## ADDED Requirements

### Requirement: Button component with variants and loading state
The system SHALL provide a `Button` component in `shared/components/ui/Button.tsx` with variants (`primary`, `secondary`, `outline`, `ghost`, `destructive`), sizes (`sm`, `md`, `lg`), a `loading` boolean prop, and `disabled` support. All variants SHALL meet WCAG AA contrast (4.5:1 for text).

#### Scenario: Button renders with primary variant
- **WHEN** `<Button variant="primary">Save</Button>` is rendered
- **THEN** button displays with primary background and white text

#### Scenario: Button shows loading spinner and is disabled when loading
- **WHEN** `loading={true}` prop is passed
- **THEN** button renders a spinner icon, the text is still readable, and the button is `disabled`

#### Scenario: Disabled button cannot be interacted with
- **WHEN** `disabled={true}` is passed
- **THEN** button has `disabled` attribute and `opacity-50 cursor-not-allowed` styling

#### Scenario: Button accepts additional className via cn()
- **WHEN** caller passes `className="w-full"` to Button
- **THEN** the class is merged without conflicting with variant classes

### Requirement: Input component with error state and label
The system SHALL provide an `Input` component in `shared/components/ui/Input.tsx` that renders a `<label>` (when `label` prop is provided), an `<input>` element, and an error message paragraph (when `error` prop is provided). The input SHALL have `aria-invalid` set to `true` when an error is present.

#### Scenario: Input renders with label
- **WHEN** `<Input id="email" label="Email" />` is rendered
- **THEN** a `<label htmlFor="email">` and an `<input id="email">` are present

#### Scenario: Input shows error message and aria-invalid
- **WHEN** `error="Campo requerido"` is passed
- **THEN** a `role="alert"` paragraph with the error text appears, and `aria-invalid="true"` is set on the input

#### Scenario: Input with type="password" masks characters
- **WHEN** `type="password"` is passed
- **THEN** input renders with type password, masking the entered characters

### Requirement: Card compound component
The system SHALL provide `Card`, `CardHeader`, `CardContent`, and `CardFooter` components in `shared/components/ui/Card.tsx` using a compound-component pattern. Each sub-component SHALL accept `className` for overrides.

#### Scenario: Card renders with header, content, and footer
- **WHEN** all four sub-components are composed together
- **THEN** they render as nested divs with appropriate spacing

#### Scenario: Card accepts custom className
- **WHEN** `<Card className="shadow-lg">` is rendered
- **THEN** `shadow-lg` is merged into the card's class list

### Requirement: Modal component with focus trap and keyboard dismiss
The system SHALL provide a `Modal` component in `shared/components/ui/Modal.tsx` that uses the native `<dialog>` element (or `role="dialog"` with `aria-modal`), traps focus within the modal while open, and closes on `Escape` key press or when an `onClose` callback is called.

#### Scenario: Modal renders children when isOpen is true
- **WHEN** `isOpen={true}` is passed
- **THEN** the modal content is visible and `aria-modal="true"` is set

#### Scenario: Modal is not rendered when isOpen is false
- **WHEN** `isOpen={false}` is passed
- **THEN** the modal is not visible (hidden or unmounted)

#### Scenario: Modal calls onClose on Escape key press
- **WHEN** the modal is open and user presses `Escape`
- **THEN** the `onClose` callback is invoked

#### Scenario: Modal calls onClose on backdrop click
- **WHEN** the modal is open and user clicks the backdrop area
- **THEN** the `onClose` callback is invoked

### Requirement: Badge component with semantic color variants
The system SHALL provide a `Badge` component in `shared/components/ui/Badge.tsx` with variants: `default`, `success`, `warning`, `error`, `info`. Each variant SHALL use semantic color tokens from the design system.

#### Scenario: Badge renders with success variant
- **WHEN** `<Badge variant="success">Activo</Badge>` is rendered
- **THEN** badge displays with green background and text

#### Scenario: Badge renders with error variant
- **WHEN** `<Badge variant="error">Inactivo</Badge>` is rendered
- **THEN** badge displays with red background and text

### Requirement: Skeleton loading placeholder
The system SHALL provide a `Skeleton` component in `shared/components/ui/Skeleton.tsx` that renders an animated pulsing placeholder. It SHALL accept `className` to control shape and size, and a `variant` prop (`text`, `circle`, `rect`).

#### Scenario: Skeleton renders animated pulse
- **WHEN** `<Skeleton className="h-4 w-32" />` is rendered
- **THEN** a div with `animate-pulse` and `bg-muted` classes is present

#### Scenario: Skeleton circle variant renders rounded
- **WHEN** `<Skeleton variant="circle" className="w-10 h-10" />` is rendered
- **THEN** the element has `rounded-full` class applied

### Requirement: cn() utility for class merging
The system SHALL provide a `cn()` utility function in `shared/lib/utils.ts` that merges Tailwind class strings using `clsx` and `tailwind-merge`, resolving conflicting utility classes in favour of the last-supplied class.

#### Scenario: cn() merges non-conflicting classes
- **WHEN** `cn("px-4", "py-2")` is called
- **THEN** the result is `"px-4 py-2"`

#### Scenario: cn() resolves conflicting Tailwind classes
- **WHEN** `cn("bg-primary", "bg-red-500")` is called
- **THEN** the result is `"bg-red-500"` (last wins)
