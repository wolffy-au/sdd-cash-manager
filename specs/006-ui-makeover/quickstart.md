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
   - Vitest covers MVVM hooks; Playwright integration specs live under `tests/ui` and hit the mocked reconciliation endpoints via Axios.
4. Build for staging
   ```bash
   npm run build
   ```
   - The production bundle remains under 1MB and serves static assets from `frontend/dist/`.
