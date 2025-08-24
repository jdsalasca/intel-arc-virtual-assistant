# Repository Guidelines

## Project Structure & Module Organization
- `api/`: FastAPI routes and request/response schemas.
- `core/`: Exceptions, interfaces, and shared domain models.
- `services/`: Business logic, orchestration, validators.
- `providers/`: Model, tool, and voice adapters (OpenVINO, search, TTS).
- `config/`: Settings and environment handling.
- `web/`: Templates and static assets (if UI is used).
- `tests/`: Test suites (`unit/`, `integration/`, `performance/`, `benchmarks/`).
- `data/`, `fixtures/`, `cache/`, `logs/`: Local assets, test fixtures, model/cache dirs, and logs.

## Build, Test, and Development Commands
- Install deps: `pip install -r requirements.txt`
- Run server: `python start_server.py --host 0.0.0.0 --port 8000`
- Run assistant (text): `python ai_assistant_brain.py --text-only`
- All tests: `python run_tests.py --all` or `pytest -v` (see markers below)
- Coverage report: `pytest --cov=core --cov=services --cov=providers --cov=config`
- Docker: `docker build -t openvino-genai-server .` then `docker run -p 8000:8000 openvino-genai-server`

## Coding Style & Naming Conventions
- Python, PEP 8, 4-space indentation; type hints encouraged.
- Modules/functions: `snake_case`; classes: `CamelCase`; constants: `UPPER_SNAKE_CASE`.
- Keep functions small and focused; prefer explicit over implicit.
- Place API contracts in `api/schemas`; shared types in `core/models`.

## Testing Guidelines
- Framework: `pytest` with markers: `unit`, `integration`, `performance`, `benchmark`, `intel`, `slow`, `gpu`, `npu`, `network`.
- Discovery: files `test_*.py`; default path `tests/` (see `pytest.ini`).
- Coverage: threshold 80%; HTML report at `tests/coverage/`, XML at `tests/coverage.xml`.
- Examples:
  - Unit only: `pytest tests/unit -m "unit or not slow"`
  - Integration: `pytest tests/integration -m integration`

## Commit & Pull Request Guidelines
- Commits follow Conventional Commits (e.g., `feat(core): add provider interface`, `fix(api): handle 400s`).
- PRs include: clear description, linked issues, test evidence (logs or screenshots), and impact notes (API, config, or perf).
- Add/adjust tests with behavior changes; keep diffs minimal and localized.

## Security & Configuration Tips
- Use `.env` (based on `.env.example`) for secrets; never commit real keys.
- API key auth is optional; when enabled, send `Authorization: Bearer <token>`.
- Prefer GPU where available (`DEVICE=GPU`); set cache dirs via `MODEL_CACHE_DIR`/`OPENVINO_CACHE_DIR` during tests.

