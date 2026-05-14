## ADDED Requirements

### Requirement: Filter panel does not occupy layout space when collapsed on mobile
On mobile viewports (below `md` breakpoint), the filter panel (`FilterBar` aside) SHALL be completely removed from the document layout flow when collapsed. The product grid SHALL occupy 100% of the available width on mobile when the filter is closed. A hamburger trigger button SHALL be rendered above the product area to open the filter panel as a fixed overlay.

#### Scenario: Mobile — filter closed by default
- **WHEN** the viewport is below the `md` breakpoint and the page loads
- **THEN** the product grid SHALL span full width and no filter-related whitespace SHALL appear above or beside the products

#### Scenario: Mobile — user opens filter
- **WHEN** the user taps the filter trigger button on mobile
- **THEN** the filter panel SHALL appear as a fixed overlay above the page content with a backdrop overlay

#### Scenario: Mobile — user closes filter via button
- **WHEN** the user taps the close button or backdrop overlay
- **THEN** the filter panel SHALL collapse and products SHALL return to full width

#### Scenario: Desktop — filter always visible
- **WHEN** the viewport is at or above the `md` breakpoint
- **THEN** the filter sidebar SHALL be permanently visible, occupying 1/4 of the grid width alongside the 3/4 products area

### Requirement: Filter sections have consistent visual hierarchy
The `FilterBar`, `CategoryFilter`, and `AllergenFilter` components SHALL use `@theme` semantic tokens exclusively for all colors and spacing. Section titles SHALL use `text-sm font-semibold text-foreground` typography. Filter sections inside `FilterBar` SHALL be separated by `<hr className="border-border" />` dividers. Checkbox inputs SHALL use `accent-primary` to apply the theme colour. Label hover states SHALL use `hover:bg-muted/50 rounded` for consistent interaction feedback.

#### Scenario: Filter sections are visually separated
- **WHEN** the filter panel is open and contains both Categories and Allergen Exclusions sections
- **THEN** a visible horizontal separator SHALL appear between each section

#### Scenario: Checkboxes reflect theme accent colour
- **WHEN** a category or allergen checkbox is checked
- **THEN** the checkbox fill colour SHALL match the `primary` design token colour

#### Scenario: Label hover provides visual feedback
- **WHEN** the user hovers over a category or allergen label row
- **THEN** the row background SHALL transition to `bg-muted/50`

#### Scenario: Filter is accessible via keyboard
- **WHEN** the user navigates filter checkboxes with Tab and activates with Space
- **THEN** each checkbox SHALL toggle correctly and have a visible focus ring (`focus:ring-2 focus:ring-ring`)
