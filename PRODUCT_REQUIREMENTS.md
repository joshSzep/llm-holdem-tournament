# LLM Hold'Em Tournament - Product Requirements

## Overview
A Texas Hold'Em poker application where a user can play against up to 5 LLM-based opponents, or watch 6 LLM-based opponents play a game fully automatically.

## Platform
- **Web Application** (browser-based)

## Visual Design

### Table Layout
- **Top-down bird's-eye view** of the poker table
- Player seats arranged around an oval table

### Card Design
- **Simple, clean card designs** — clear suit and rank, no ornate detail
- Custom card back design with app branding

### Chip Visualization
- **Numerical display** for chip counts (not stacked chip graphics)
- **Animated chip movement** when chips move to the pot (bet, call, raise)

### Color Scheme
- **Modern dark theme** throughout
- Dark background, muted table felt, accent colors for actions and highlights
- High contrast for cards, chip counts, and important information

### Animations
- **Card dealing**: Cards animate from deck to player positions
- **Chip movements**: Chips animate from player to pot, pot to winner
- **Player actions**: Visual feedback for fold, check, call, raise (e.g., cards sliding away on fold)
- **Dealer button**: Smooth movement between seats between hands
- **Community cards**: Animated reveal for flop (3 cards), turn, and river
- **Showdown**: Tiered reveal animations by hand strength (see Showdown section)
- **Overall feel**: Exciting, polished, and visually appealing

### Audio
- **No audio** — no sound effects, no background music

## Post-Game Experience

### Results Screen
- Summary screen displayed when the tournament ends showing:
  - Final standings (finishing order of all players)
  - Key stats: biggest pot, best hand, total hands played, number of bluffs, etc.

### Hand History Review
- **All games are recorded** and stored in the database
- Player can browse past games and review them **turn by turn**
- Every action and chat message is preserved and displayed in the review view
- Replay view shows the table state at each decision point

### Post-Game Options
- **Rematch**: Play again with the same opponents
- **Return to Lobby**: Go back to the setup screen to configure a new game

## Information Integrity & Cheating Prevention
- **Strict information boundary**: Each AI agent only receives information it would legitimately have in a real poker game
- **Explicit prompt validation/scrubbing** before every LLM call to ensure no private information (e.g., opponents' hole cards) is leaked
- AI agents never see other players' hole cards unless revealed at showdown
- Validation layer is a hard requirement, not optional

## Invalid Action Handling
- If an LLM returns an illegal action (e.g., raise below minimum, check when there's a bet to call):
  1. **Retry**: Send the action back to the LLM with an error message explaining why it was invalid
  2. If retry also fails, fall back to auto-check (if possible) or auto-fold
- The 30-second turn timer still applies across retries

## LLM Thinking Indicator
- While an AI agent is deciding, display a **spinning dots animation** on that player's avatar/seat
- Provides clear visual feedback that the game is waiting on an AI decision

## Avatar System

### Avatar Source
- **Pre-made static images** bundled with the app
- One unique avatar per agent in the roster
- Human player gets a **default "you" avatar**
- Human player is always displayed as **"You"** — no name customization
- No other player customization options

### Avatar Display States
- **Default**: Normal display at the seat
- **Active turn**: Glowing border when it's the player's turn
- **Folded**: Greyed out after folding for the current hand
- **Low chips**: Red border when nearly out of chips
- **Thinking**: Spinning dots overlay while AI is deciding
- **Eliminated**: Fully dimmed / removed from active play

## Error Handling & Resilience

### API Failure Recovery
- On LLM API failure (network error, rate limit, 500 error):
  1. **Retry** a few times with exponential backoff
  2. If retries exhausted, **auto-fold** that player for the hand
- Game continues uninterrupted; no pause or error dialog for transient failures

### Cost Tracking
- **Visual cost indicator** displayed in the UI
- Shows estimated API cost for the current game / cumulative session

### Provider Availability
- On startup, detect which API keys are configured
- Agents whose model provider has **no configured API key** are **hidden from the roster**
- Only agents with available providers are shown to the player during opponent selection

## Browser & Display Requirements
- **Desktop browsers only** — no mobile/tablet optimization
- **Minimum viewport**: 1280×720
- **Browser support**: Modern evergreen browsers (Chrome, Firefox, Safari, Edge)

## Development & Tooling

### Package Managers
- **Frontend**: pnpm
- **Backend**: uv

### Repository Structure
- Monorepo with separate directories: `frontend/` and `backend/`

### Task Runner
- **just** (justfile) for all commands
- Single command to start both frontend and backend in development mode
- Commands for build, test, lint, format, etc.

### Testing
- **Backend**: pytest
- **Frontend**: vitest
- **Minimum 80% test coverage** maintained at all times
- Coverage enforcement as part of the development workflow

### Linting & Code Quality
- **Backend**:
  - **Ruff** for linting + formatting
  - **ty** for type checking
- **Frontend**:
  - **ESLint** for linting
  - **Prettier** for formatting
- **Pre-commit hooks** via `pre-commit` to enforce linting/formatting before commits

### Hand Evaluation
- Use an **existing Python poker hand evaluation library** (e.g., `treys` or similar battle-tested library)
- No custom hand evaluator — rely on proven, well-tested implementations

### Logging & Observability
- **Structured logging** using Python's built-in `logging` module
- **Pydantic Logfire** integration for tracing LLM calls, costs, and performance monitoring
- Logfire provides real-time debugging, behavior tracing, and cost tracking for all AI agent interactions

## Game Modes
1. **Player Mode**: Human user plays against 1-5 LLM opponents (2-6 total players)
2. **Spectator Mode**: Watch 2-6 LLM opponents play a full game automatically

### Spectator Mode Details
- All hole cards visible (TV broadcast style)
- 30-second turn timer still applies as a safeguard
- AI turns resolve **as fast as the AI responds** (no artificial delay) — same as Player Mode
- Game plays at a natural pace
- Player can **leave and return** to a spectator game (picks up where it left off, since game state is persisted)
- **No seat takeover** — cannot switch from spectator to player mid-game

### Player Mode Details
- AI turns also resolve as fast as the AI responds (no artificial delay)
- Human player has up to 30 seconds per turn
- Player can leave and return to resume the game

### Game Pause Behavior (Both Modes)
- **Games always require a human observer** — the game **pauses** when the user disconnects (closes browser tab / loses WebSocket connection)
- Game **resumes automatically** when the user reconnects
- No actions are processed while the game is paused
- In Player Mode, the human is never auto-folded for being away — the game simply waits

### Session & Concurrency
- **One active game at a time** — cannot run multiple simultaneous games
- **One active session allowed** — if a second browser tab is opened, it should not be able to control or interfere with the existing session

## Game Format
- **Sit-and-Go (SNG) Tournament** format exclusively
- **Starting stack**: 2,000 chips per player
- Players are eliminated when they lose all chips; last player standing wins

## Blind Structure
- Blinds escalate every **10 hands**
- Approximate doubling progression (e.g., 10/20 → 20/40 → 40/80 → 75/150 → 150/300 → 300/600 → 500/1000 → 1000/2000...)
- **No antes** — blinds only throughout the tournament

## Turn Timer
- Each player (human and AI) has **30 seconds** to act on their turn
- A visible countdown timer is displayed during each player's turn
- If time expires, the player is **auto-checked** (if possible) or **auto-folded**
- Applies to both human players and LLM agents (guards against slow API responses)

## Lobby / Setup Screen
- Player chooses game mode: **Play** or **Spectate**
- Player selects number of opponents (1-5 in Play mode, 2-6 in Spectate mode)
- For each seat, the player can:
  - **Hand-pick** an opponent from the agent roster (browsing agent cards with name, avatar, backstory)
  - **Random fill** — let the system assign a random agent to that seat
- Game starts once all seats are configured

### Lobby Sections
- **New Game**: Setup screen to configure and start a new game
- **In-Progress Games**: List of paused/left games with a "Resume" button
- **Game History**: List of completed past games (e.g., "Game #12 — Feb 14, 2026 — You won against Poker Pete, Bluffing Betty, …") with option to review

## App Navigation Flow
1. **Lobby** (home screen) → New Game setup, Resume game, Game History
2. **Game Table** → Active gameplay (Player or Spectator mode)
3. **Post-Game Summary** → Results screen, then Rematch or Back to Lobby
4. **Game Review** → Turn-by-turn replay of any past game

## Tech Stack
- **Frontend**: React with TypeScript
- **Frontend build tool**: Vite
- **Frontend state management**: Zustand
- **Frontend animations**: Framer Motion
- **Backend**: Python / FastAPI
- **Styling**: Custom CSS
- **LLM Framework**: Pydantic AI (model-agnostic; supports OpenAI, Anthropic, Google, Groq, Mistral, Cohere, Bedrock, Ollama, and many more)
- **Real-time Communication**: WebSockets
- **Database**: SQLite
- **ORM**: SQLModel (Pydantic + SQLAlchemy, lightweight)
- **Migrations**: Auto-create tables on startup (no Alembic)

## LLM Configuration
- **Pre-configured AI Agents**: The backend provides a large roster (30+) of pre-built opponents, each combining a specific model selection with unique prompting to create distinct intelligences and personalities
- Players select opponents from this roster when setting up a game
- Pydantic AI abstracts away provider differences, enabling seamless multi-model play
- All supported Pydantic AI models are available (see `pydantic-ai-documentation.md` for full list)

## AI Agent Profiles
Each pre-configured agent has:
- **Name**: A unique character name
- **Avatar**: A distinct avatar image
- **Backstory / Flavor Text**: A short bio visible to the player (e.g., "Poker Pete — a retired Vegas dealer who's seen it all")
- **Personality Dimensions**:
  - **Play style**: Aggressive, tight/conservative, loose/unpredictable, mathematical/GTO, etc.
  - **Table talk style**: Trash-talker, silent type, friendly/chatty, philosophical, sarcastic, etc.
  - **Risk tolerance**: Reckless, calculated, cautious
  - **Bluffing tendency**: Frequent bluffer, honest player, deceptive
- These traits are encoded into each agent's system prompt, shaping both gameplay decisions and chat behavior

## UI Components
- Poker table (top-down or angled view) with player positions
- Player avatars at each seat
- Card rendering (hole cards, community cards)
- Chip stacks / bet visualization
- Chat/Action log window (combined table talk + game action history)

## Player Controls (Human Turn)
- **Action buttons**: Fold, Check, Call, Raise/Bet
- **Raise controls**:
  - Preset buttons: Min Raise, 2x, 3x, Pot, All-In
  - Slider for custom raise amount
- Controls are only active during the human player's turn

## Card Visibility
- **Player Mode**: Human's hole cards always face-up; opponents' cards hidden until showdown
- **Spectator Mode**: All hole cards visible (TV broadcast style) so the viewer can follow the action

## Chat System
- **Single interleaved stream** — chat messages and game actions (e.g., "Poker Pete raises to 400") are displayed chronologically in one unified log
- Human player can type messages to talk to AI opponents
- AI agents **may or may not** respond to human chat — it's up to their personality/prompting
- AI agents **may or may not** respond to each other's chat as well
- Chat messages from AIs reflect their personality (trash talk, friendly banter, silence, etc.)

### AI Chat Architecture
- **Chat is never bundled with game actions** — action responses contain only the action (fold/check/call/raise)
- **Reactive chat system**: After key game events, the backend gives AI agents an opportunity to comment via a separate, lightweight LLM call
- Key trigger events for chat opportunities: all-ins, showdowns, eliminations, big pots, surprising plays, and when a human sends a chat message
- Not every AI reacts to every event — personality and randomness determine who speaks up
- Chat should feel **organic and natural**, not mechanical or predictable
- Conservative with API costs: only trigger chat opportunities at meaningful moments, not after every single action

### Chat by Game Mode
- **Player Mode**: Human can type and send chat messages; AI agents may respond
- **Spectator Mode**: Chat input is **disabled** for the viewer; the log shows AI-to-AI banter and game actions only

## LLM Decision-Making

### Input (Structured message to LLM each turn)
- Agent's hole cards
- Community cards (flop/turn/river as applicable)
- Current pot size
- Current bet to call
- Agent's own chip stack
- All opponents' chip stacks
- Betting action history for the current hand
- Recent chat messages
- Full hand history from prior hands in the session
- **No pre-computed opponent tendencies** — the AI must form its own reads from raw history

### Output (Structured via Pydantic AI)
- Guaranteed valid, parseable response every time using Pydantic models
- **Action response** (game decision call):
  - **Action**: fold, check, call, raise/bet
  - **Amount**: (if raise/bet) the raise amount
- **Chat response** (separate reactive chat call):
  - **Chat message**: table talk text to display in the chat window
  - **Or empty**: agent chooses not to speak

### Memory
- AI agents **remember all previous hands** within the current session/tournament
- Hand history is included in the context provided to the LLM on each turn
- Allows agents to adapt strategy, develop reads, and reference past events in chat

### Context Window Management
- **Default behavior**: Send full hand history to the LLM on every turn
- **Context limit awareness**: The system tracks each model's context window size
- **Graceful truncation**: When approaching a model's context limit, **truncate the oldest hands first** to fit within the window
- Prefer models with large context windows for the best experience
- Current hand and recent history are always prioritized over older hands

## Communication Protocol
- **WebSockets** for real-time bidirectional communication between React frontend and FastAPI backend
- All game events streamed to the frontend in real-time: card deals, bets, chat messages, timer updates, etc.
- Player actions (fold, check, call, raise, chat) sent from frontend to backend over WebSocket
- **Typed message protocol**: Clear TypeScript types on the frontend and Pydantic models on the backend for end-to-end type safety
- **Full game state** sent on every update (simplicity over efficiency — game state is small enough)

## Game State Management
- **Backend is the single source of truth** for all game state
  - Deck, shuffling, dealing
  - Hole cards, community cards
  - Pot calculation, side pots
  - Chip stacks
  - Blind levels, hand count
  - Turn order, player elimination
- Frontend is a **pure renderer** — receives state updates and displays them, performs no game logic

## Persistence
- All game state is stored in a **SQLite database** on the backend
- Games are **saveable and resumable** — if the browser is closed, the player can return and continue
- Full hand history is persisted for AI context and potential post-game review

## Deployment & Authentication
- **Single player, local application** — no user authentication required
- Not intended for public deployment
- **API keys** are provided by the server operator via environment variables or a `.env` file
- No per-user API key management needed

## Poker Rules & Edge Cases

### Core Rules
- Standard **Texas Hold'Em No-Limit** rules
- Standard **dealer button rotation** with small blind / big blind positions
- Standard **heads-up rules** when down to 2 players (dealer posts SB, acts first pre-flop, last post-flop)

### Side Pots
- **Fully implemented from the start**
- Correct side pot calculation when one or more players are all-in with different stack sizes
- Clear visual display of main pot and all side pots

### Split Pots
- Properly handled when players have identical hand rankings
- Chips divided evenly; odd chip goes to first player after the dealer button

### Showdown
- Display **proper hand evaluation** text (e.g., "Full House, Kings full of Sevens")
- **Brief reveal animation** for hole cards at showdown
- **Tiered animations by hand strength** — more impressive hands get more dramatic animations:
  - Royal Flush: most spectacular
  - Straight Flush, Four of a Kind, Full House: impressive
  - Flush, Straight, Three of a Kind: moderate
  - Two Pair, One Pair: subtle
  - High Card: minimal
