# Research: UI Makeover

## Decision: Frontend as React + Vite single-page app
**Rationale**: React 18 with Vite delivers fast hot reload, tree-shaking, and integrates easily with MVVM-style hooks/stores we need for the ledger/reconciliation flows. The tooling has mature virtualization components (e.g., react-virtual) and good accessibility support.
**Alternatives considered**: SvelteKit for built-in reactivity (more recent but smaller ecosystem) and Angular for built-in structure (heavier bundle). React scored higher due to existing team familiarity and ecosystem speed.

## Decision: MVVM-inspired state via Zustand/xState stores
**Rationale**: The spec demands observable view models decoupled from the DOM, so we centralize ledger/reconciliation state in focused stores and expose commands to components rather than letting them manage individual API calls.
**Alternatives considered**: Managing state purely with React Context (too noisy for virtualization) or Redux Toolkit (boilerplate-heavy) — Zustand/xState blend gives clarity and minimal ceremony.

## Decision: Virtualized ledger/register lists + badges for statuses
**Rationale**: To keep the UI responsive with 250+ rows, virtualization keeps render counts low and the Difference badge refresh remains under the 1s load budget. Badges ingest backend statuses (UNCLEARED/CLEARED/RECONCILED) to fulfill FR-003.
**Alternatives considered**: Pagination (slows browsing and breaks GNucash feel) and server-side rendering (not necessary for interactive matching). Virtualization with incremental loading satisfies responsiveness requirements.

## Decision: Accessible discrepancy guidance panel
**Rationale**: The non-zero Difference experience now communicates the remaining UNCLEARED count with icons, copy, and a consistent accent bar so auditors immediately understand what action to take. High contrast outlines (`insight-under`, `insight-over`) plus the `Highlight UNCLEARED rows` action keep the component legible at small sizes.
**Alternatives considered**: Using tooltips or plain badges (dropped because they lacked context) or relying on modal dialogs (too interruptive). The lightweight panel stays in the flow and backs its color decisions with the Tailwind contrast checks recorded in layout.css.
