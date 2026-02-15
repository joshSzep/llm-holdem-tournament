# AI Agent Development Guide

Instructions for GitHub Copilot and other AI coding agents working on this project.

## Project Context

This is **LLM Hold'Em Tournament** — a Texas Hold'Em poker web app where a human plays against (or spectates) LLM-powered AI opponents. Read these files for full context:

- `PRODUCT_REQUIREMENTS.md` — Complete product specification
- `ARCHITECTURE.md` — System design, directory structure, data models, protocols
- `ROADMAP.md` — Phased implementation plan with granular tasks

## Repository Structure

```
llm-holdem-tournament/
├── backend/           # Python + FastAPI (uv)
│   ├── src/llm_holdem/   # Application source
│   └── tests/            # pytest tests
├── frontend/          # React + TypeScript (pnpm, Vite)
│   └── src/              # Application source
├── justfile           # All project commands
└── .env               # API keys (not committed)
```

## Tech Stack Rules

### Backend (Python)
- **Python 3.12+**
- **FastAPI** for HTTP and WebSocket endpoints
- **Pydantic AI** for all LLM interactions — never call LLM APIs directly
- **SQLModel** for database models (Pydantic + SQLAlchemy)
- **SQLite** via aiosqlite for async database access
- **uv** as the package manager — use `uv add` to add dependencies
- **Ruff** for linting and formatting
- **ty** for type checking
- **pytest** for testing with ≥80% coverage

### Frontend (TypeScript)
- **React 18+** with functional components and hooks only — no class components
- **TypeScript** strict mode — no `any` types unless absolutely unavoidable
- **Vite** for build tooling
- **Zustand** for state management — no Redux, no React Context for global state
- **Framer Motion** for all animations
- **Custom CSS** — no CSS frameworks (no Tailwind, no Bootstrap, no CSS-in-JS)
- **pnpm** as the package manager
- **ESLint + Prettier** for linting and formatting
- **vitest** for testing with ≥80% coverage

## Coding Conventions

### Python

- Use `async`/`await` throughout — the backend is fully async
- All API models use **Pydantic BaseModel** with strict typing
- All database models use **SQLModel** 
- Use Python's built-in `logging` module for all logging — no `print()` statements
- Type annotate all function signatures and return types
- Use `Literal` types for enums where practical (e.g., `Literal["fold", "check", "call", "raise"]`)
- Docstrings on all public functions and classes (Google style)
- Import sorting handled by Ruff — don't manually organize imports
- Use `pathlib.Path` over `os.path`

### TypeScript

- All components are functional with explicit return types
- Props interfaces defined above the component, named `{ComponentName}Props`
- Use `const` by default; `let` only when reassignment is necessary
- Prefer early returns over nested conditionals
- CSS class names use kebab-case (e.g., `player-seat`, `action-buttons`)
- One component per file; filename matches component name (PascalCase)
- Custom hooks prefixed with `use` in `hooks/` directory
- All WebSocket message types defined in `types/messages.ts`
- All game state types defined in `types/game.ts` — must mirror backend Pydantic models

### CSS

- Use CSS custom properties (variables) for all colors, spacing, and typography
- Dark theme: define palette in `:root` in `App.css`
- BEM-like naming: `.component-name`, `.component-name__element`, `.component-name--modifier`
- No inline styles except for truly dynamic values (positions, computed sizes)
- Media queries not needed — desktop only, 1280×720 minimum

## Architecture Principles

### Backend is the single source of truth
The frontend **never** computes game logic. It receives full game state from the backend and renders it. All validation, card dealing, pot calculation, and turn management happens server-side.

### Information integrity is non-negotiable
Every LLM prompt **must** pass through the prompt validator before being sent. The validator strips opponent hole cards and asserts only legitimate information is included. Never bypass this — it's a hard gate, not advisory.

### Structured LLM I/O
All LLM interactions use Pydantic AI's structured output. Define clear Pydantic models for both action decisions and chat responses. Never parse free-text LLM output manually.

### Game actions and chat are separate LLM calls
The action agent returns only a game action (fold/check/call/raise + amount). Chat is handled by a separate reactive chat agent triggered after key events. Never bundle chat with actions.

### Full game state over WebSocket
Send the complete game state on every update. Don't implement delta/patch updates. The game state is small enough that full state is simpler and more reliable.

## Testing Requirements

- **Minimum 80% code coverage** at all times — this is enforced
- Write tests alongside implementation, not after
- Backend tests use **pytest** with async support (`pytest-asyncio`)
- Frontend tests use **vitest** with React Testing Library
- Game engine tests should cover edge cases thoroughly:
  - Heads-up blind rules
  - Side pots with multiple all-ins
  - Split pots
  - Blind escalation boundaries
  - All hand types and tie-breakers
- Mock LLM calls in tests — never make real API calls in tests
- Use fixtures and factories for test data

## Common Tasks

### Adding a new agent to the roster
1. Add the profile to `backend/src/llm_holdem/agents/profiles.py`
2. Include: id, name, avatar filename, backstory, model, provider, personality dimensions
3. Write action and chat system prompts that reflect the personality
4. Add a corresponding avatar image to `frontend/public/avatars/`

### Adding a new REST endpoint
1. Add the route to `backend/src/llm_holdem/api/routes.py`
2. Define request/response models in `backend/src/llm_holdem/api/schemas.py`
3. Add corresponding TypeScript types in `frontend/src/types/api.ts`
4. Write tests in `backend/tests/test_api/`

### Adding a new WebSocket message type
1. Add the Pydantic model to backend schemas
2. Add the TypeScript type to `frontend/src/types/messages.ts`
3. Handle in the WebSocket handler (backend) and `useWebSocket` hook (frontend)
4. Update Zustand store if the message carries state

### Running the project
```bash
just dev        # Start frontend + backend
just test       # Run all tests
just lint       # Lint everything
just format     # Format everything
```

## Do NOT

- Do not use `any` in TypeScript
- Do not use class components in React
- Do not add CSS frameworks or utility-class libraries
- Do not call LLM APIs directly — always use Pydantic AI agents
- Do not put game logic in the frontend
- Do not skip the prompt validator for LLM calls
- Do not use `print()` for logging in Python
- Do not create database migration files — tables auto-create on startup
- Do not add authentication or multi-user features
- Do not add audio/sound effects
- Do not optimize for mobile or tablet viewports
- Do not bundle chat responses with action responses in LLM calls
- Do not use relative imports in Python — always use absolute imports from the project root
- Do not group multiple imports on the same line in Python — one import per line
