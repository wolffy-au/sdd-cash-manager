# Quickstart: UI Makeover

1. Install frontend tooling
   ```bash
   cd frontend
   npm install
   ```
2. Run the development server
   ```bash
   npm run dev -- --host 0.0.0.0 --port 4173
   ```
   - The ledger workspace listens to `/accounts` and `/reconciliation/sessions` endpoints on the FastAPI backend (usually `http://127.0.0.1:8000`).
3. Run the component test suite
   ```bash
   npm run test:ui
   ```
   - Vitest now covers ledger, reconciliation, and the new discrepancy insight guidance panel, while Playwright verifies the reconciliation workflow and highlights UNCLEARED filtering.
   - In this container, Playwright attempts to launch Chromium and currently fails because the runtime lacks `libatk-1.0.so.0`. Install the matching system dependencies (e.g., `libatk1.0-0`, `libatk-bridge2.0-0`, `libgtk-3-0`) before re-running `npm run test:ui` to see the three Playwright flows succeed.
4. Build for staging
   ```bash
   npm run build
   ```
   - The production bundle remains under 1MB and serves static assets from `frontend/dist/`.
