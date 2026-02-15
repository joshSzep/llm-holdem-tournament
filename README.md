# LLM Hold'Em Tournament

A Texas Hold'Em poker web application where you play against AI opponents powered by large language models — or sit back and watch them battle it out.

## What Is This?

LLM Hold'Em Tournament pits you against a roster of 30+ AI poker players, each with a unique personality, play style, and backstory. Every opponent is driven by a real LLM (GPT-4o, Claude, Gemini, Mistral, and more), making decisions and trash-talking at the table just like a human would.

**Play Mode** — Take a seat and play heads-up or at a full table against 1–5 AI opponents.

**Spectator Mode** — Set up a table of 2–6 AI players and watch them go at it, with all hole cards visible like a TV broadcast.

All games are Sit-and-Go tournaments with 2,000 starting chips and escalating blinds. The last player standing wins.

## Features

- **30+ AI opponents** with distinct personalities — aggressive bluffers, cautious grinders, trash-talkers, silent assassins, and everything in between
- **Model-agnostic** — opponents run on OpenAI, Anthropic, Google, Groq, Mistral, Ollama, and more via Pydantic AI
- **Reactive table talk** — AI players banter, react to big hands, and respond to your chat messages organically
- **Full poker rules** — side pots, split pots, heads-up play, proper blind structure, hand evaluation
- **Animated UI** — card dealing, chip movements, tiered showdown animations (a royal flush looks a lot more exciting than a pair)
- **Game history & replay** — every game is saved; review any past game turn by turn with full action and chat history
- **Save & resume** — leave a game and come back to it later
- **Cost tracking** — see estimated API costs in real-time

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- [just](https://github.com/casey/just) task runner
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [pnpm](https://pnpm.io/) (Node.js package manager)
- At least one LLM provider API key

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/llm-holdem-tournament.git
   cd llm-holdem-tournament
   ```

2. **Configure API keys:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your API keys. You only need keys for the providers you want to use — agents for unconfigured providers are automatically hidden from the roster.

   ```bash
   # Add any/all of these:
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   GOOGLE_API_KEY=...
   GROQ_API_KEY=gsk_...
   MISTRAL_API_KEY=...

   # For local models (no key needed):
   OLLAMA_BASE_URL=http://localhost:11434

   # Optional observability:
   LOGFIRE_TOKEN=...
   ```

3. **Install dependencies:**
   ```bash
   just install
   ```

4. **Start the app:**
   ```bash
   just dev
   ```

5. **Open your browser** to [http://localhost:5173](http://localhost:5173)

## How to Play

1. **Lobby** — Choose **Play** or **Spectate**, then pick your opponents from the roster. Each agent card shows their name, avatar, and backstory. Leave any seat set to "Random" for a surprise.

2. **Game Table** — Play standard No-Limit Texas Hold'Em. Use the action buttons (Fold, Check, Call, Raise) and raise slider when it's your turn. You have 30 seconds per decision. Type in the chat window to talk to the AIs — some of them might talk back.

3. **Post-Game** — See final standings and stats (biggest pot, best hand, and more). Hit **Rematch** to play the same opponents again, or head back to the lobby.

4. **Review** — Browse any past game from the lobby's Game History section. Step through every hand action by action, with all cards and chat messages preserved.

## Available Commands

| Command | Description |
|---------|-------------|
| `just dev` | Start frontend and backend in development mode |
| `just test` | Run all tests (backend + frontend) |
| `just lint` | Run all linters |
| `just format` | Format all code |
| `just install` | Install all dependencies |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, TypeScript, Vite, Zustand, Framer Motion |
| Backend | Python, FastAPI, Pydantic AI, SQLModel |
| Database | SQLite |
| Real-time | WebSockets |
| LLM Integration | Pydantic AI (OpenAI, Anthropic, Google, Groq, Mistral, Ollama, and more) |
| Observability | Python logging, Pydantic Logfire |

## Project Structure

```
llm-holdem-tournament/
├── frontend/          # React + TypeScript UI
├── backend/           # Python + FastAPI server
├── justfile           # Task runner commands
├── .env.example       # Environment variable template
├── PRODUCT_REQUIREMENTS.md
├── ARCHITECTURE.md
└── ROADMAP.md
```

## License

See [LICENSE](LICENSE) for details.
