# Implementation Plan: UI Makeover

**Branch**: `006-ui-makeover` | **Date**: 2026-03-23 | **Spec**: [../spec.md](../spec.md)
**Input**: Feature specification from `/specs/006-ui-makeover/spec.md`

## Summary
Deliver a React/Vite-based front-end that mirrors a GnuCash-style ledger workspace, reconciliation kit, and discrepancy insights panel while wiring the view models to the existing FastAPI reconciliation surface. The UI will leverage MVVM-inspired observables + reducers, virtualization for long lists, and responsive layout techniques so users can browse accounts, match statement transactions, and watch the Difference badge animate without page reloads.

## Technical Context
**Language/Version**: TypeScript 5.7 (frontend) alongside the existing Python 3.12 FastAPI backend
**Primary Dependencies**: React 18 + Vite for bundling, Zustand or xState for MVVM state, Axios for REST calls, Tailwind CSS for layout, FastAPI/SQLAlchemy for backend APIs
**Storage**: Ephemeral client state (Zustand store/session storage) synced with FastAPI sessions; no persistent storage added on the frontend
**Testing**: Vitest + Playwright for UI components and flows; pytest already covers backend contracts
**Target Platform**: Modern desktop browsers (Chromium, Firefox, Safari) with responsive behavior for tablets
**Project Type**: Web application (frontend)
**Performance Goals**: Ledger and reconcile panels hydrate within 1 second with up to 250 transaction rows, virtualization keeps scrolling fluid, and Difference updates happen without visible jitter
**Constraints**: Responsive layout, keyboard-accessible controls, virtualization for large datasets, accessible badges/warnings, and maintainable separation between view and business logic
**Scale/Scope**: Supports finance operators working across dozens of accounts with per-session reconciliations (up to 250 rows) and multi-pane context (tree/register/detail) without blocking the backend

## Constitution Check
*GATE: Code Quality (I), Testing (II), UX Consistency (III), Performance (IV), Security (V), State Management (VI) are satisfied.*
Example: MVVM-style stores keep logic decoupled (Code Quality + State), Vitest tests cover every component (Testing), UX builds on GNucash mental model (UX Consistency), virtualization + badge timing keep updates <200ms (Performance), Frontend calls remain authenticated and sanitize input (Security), and state transitions for reconciliation follow documented flows (State Management).

## Project Structure
### Documentation (this feature)
```text
specs/006-ui-makeover/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code
```text
frontend/
├── package.json
├── public/
└── src/
    ├── components/
    │   ├── ledger/
    │   ├── reconciliation/
    │   └── guidance/
    ├── features/
    │   ├── ledger.tsx
    │   └── reconciliation.tsx
    ├── hooks/
    │   ├── useVirtualizedList.ts
    │   └── useReconciliationViewModel.ts
    ├── stores/
    │   ├── ledgerStore.ts
    │   └── reconciliationStore.ts
    └── styles/
        └── layout.css
tests/
└── ui/
    ├── ledger.spec.ts
    └── reconciliation.spec.ts
```
**Structure Decision**: We treat the UI makeover as a dedicated frontend application (`frontend/`) that will fetch from the existing FastAPI backend. Components and hooks live under `frontend/src` with dedicated directories for ledger, reconciliation, and guidance, while Playwright/Vitest lives under `tests/ui`. This keeps the new UI modular and aligned with MVVM boundaries described in the spec.

## Complexity Tracking
> No constitution violations detected; complexity table not required.
