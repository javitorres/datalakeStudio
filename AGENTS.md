# Repository Guidelines

## Project Structure & Module Organization
- `client/`: Vue 3 + Vite frontend. Main app code is in `client/src/` with UI components in `client/src/components/`, shared helpers in `client/src/lib/`, and static assets in `client/src/assets/`.
- `server/`: FastAPI backend. Entry point is `server/server.py`; API routers live in `server/routes/`, service logic in `server/services/`, and DTO/models in `server/model/`.
- `sampleData/`: local datasets for manual exploration and demos.
- Root-level `docker-compose.yml` starts both frontend and backend together.

## Build, Test, and Development Commands
- Full stack with Docker:
  - `docker-compose up --build` (builds and runs frontend on `:8080`, backend on `:8000`).
- Backend local dev:
  - `cd server && pip3 install -r requirements.txt`
  - `python3 server.py` (runs FastAPI via Uvicorn using `config.yml`).
- Frontend local dev:
  - `cd client && npm install`
  - `npm run dev -- --port 8080` (Vite dev server)
  - `npm run build` (production bundle)
  - `npm run lint` (ESLint with auto-fix)

## Coding Style & Naming Conventions
- JavaScript/Vue: follow ESLint (`client/package.json`), 2-space indentation, component files in PascalCase (example: `TableInspector.vue`), utility modules in camelCase/PascalCase as already used in `client/src/lib/`.
- Python: PEP 8 style, 4-space indentation, snake_case for functions/modules, and keep router/service split consistent (`routes/*_controller.py`, `services/*Service.py`).
- Keep changes focused; avoid broad refactors in feature/fix PRs.

## Testing Guidelines
- There is currently no committed automated test suite. Minimum requirement is manual smoke validation for both apps:
  - frontend: load app, run a query flow, verify key panels render.
  - backend: hit core endpoints (database load/query/API routes) after startup.
- If you add tests, place frontend tests under `client/src/**/__tests__/` and backend tests under `server/tests/` using `test_*.py` naming.

## Commit & Pull Request Guidelines
- Existing history favors short, imperative commit subjects (examples: `Upgrade versions`, `Fixed error on H3 plots...`). Use clear, single-purpose commits.
- Recommended format: `<type>: <brief summary>` (example: `fix: handle empty endpoint list`).
- PRs should include:
  - what changed and why,
  - impacted areas (`client`, `server`, or both),
  - manual test steps and results,
  - screenshots/GIFs for UI-visible changes.

## Security & Configuration Tips
- Never commit secrets. Use `server/secrets.yml.template` as the baseline and keep real credentials in local `secrets.yml` only.
- Validate `server/config.yml` before running; default database path and port must match your local setup.
