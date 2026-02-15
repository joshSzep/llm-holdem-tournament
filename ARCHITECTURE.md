# LLM Hold'Em Tournament - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (Desktop)                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              React + TypeScript Frontend                   │  │
│  │  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌───────────────┐   │  │
│  │  │  Lobby   │ │  Game    │ │  Post  │ │ Game Review   │   │  │
│  │  │  Screen  │ │  Table   │ │  Game  │ │ (Replay)      │   │  │
│  │  └─────────┘ └──────────┘ └────────┘ └───────────────┘   │  │
│  │  ┌─────────────────────┐  ┌────────────────────────────┐  │  │
│  │  │  Zustand Store      │  │  Framer Motion Animations  │  │  │
│  │  └─────────────────────┘  └────────────────────────────┘  │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         │ WebSocket (JSON)                       │
└─────────────────────────┼───────────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────────┐
│                         │        Backend Server                  │
│  ┌──────────────────────▼────────────────────────────────────┐  │
│  │                 FastAPI + WebSocket Server                  │  │
│  │  ┌────────────┐  ┌──────────────┐  ┌───────────────────┐  │  │
│  │  │  REST API   │  │  WebSocket   │  │  Session Manager  │  │  │
│  │  │  (Lobby,    │  │  Handler     │  │  (1 active game)  │  │  │
│  │  │  History)   │  │  (Game I/O)  │  │                   │  │  │
│  │  └────────────┘  └──────────────┘  └───────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     Game Engine                            │  │
│  │  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌────────────┐  │  │
│  │  │  Dealer   │ │  Betting  │ │  Pot     │ │  Hand      │  │  │
│  │  │  (Deck,   │ │  Manager  │ │  Manager │ │  Evaluator │  │  │
│  │  │  Cards)   │ │           │ │  (Side   │ │  (treys)   │  │  │
│  │  │          │ │           │ │   Pots)  │ │            │  │  │
│  │  └──────────┘ └───────────┘ └──────────┘ └────────────┘  │  │
│  │  ┌──────────┐ ┌───────────┐ ┌──────────────────────────┐  │  │
│  │  │  Blind   │ │  Turn     │ │  Tournament Manager      │  │  │
│  │  │  Manager │ │  Manager  │ │  (Elimination, Standings)│  │  │
│  │  └──────────┘ └───────────┘ └──────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   AI Agent Layer                           │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌───────────────────┐  │  │
│  │  │  Agent        │ │  Prompt      │ │  Context Window   │  │  │
│  │  │  Registry     │ │  Builder &   │ │  Manager          │  │  │
│  │  │  (30+ agents) │ │  Validator   │ │                   │  │  │
│  │  └──────────────┘ └──────────────┘ └───────────────────┘  │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌───────────────────┐  │  │
│  │  │  Action       │ │  Chat        │ │  Pydantic AI      │  │  │
│  │  │  Agent        │ │  Agent       │ │  Integration      │  │  │
│  │  │  (Decisions)  │ │  (Reactive)  │ │                   │  │  │
│  │  └──────────────┘ └──────────────┘ └───────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   Data Layer                               │  │
│  │  ┌──────────────┐ ┌──────────────────────────────────────┐ │  │
│  │  │  SQLModel     │ │  SQLite Database                     │ │  │
│  │  │  Models       │ │  ┌──────────┐ ┌──────────┐          │ │  │
│  │  │              │ │  │  Games   │ │  Hands   │          │ │  │
│  │  │              │ │  ├──────────┤ ├──────────┤          │ │  │
│  │  │              │ │  │  Players │ │  Actions │          │ │  │
│  │  │              │ │  ├──────────┤ ├──────────┤          │ │  │
│  │  │              │ │  │  Chat    │ │  Config  │          │ │  │
│  │  └──────────────┘ │  └──────────┘ └──────────┘          │ │  │
│  │                    └──────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Observability: Python logging + Pydantic Logfire          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  LLM Providers (via Pydantic AI)                           │  │
│  │  OpenAI | Anthropic | Google | Groq | Mistral | Ollama ... │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
llm-holdem-tournament/
├── justfile                        # Task runner commands
├── .pre-commit-config.yaml         # Pre-commit hook config
├── .env.example                    # Example environment variables
├── PRODUCT_REQUIREMENTS.md
├── ARCHITECTURE.md
├── ROADMAP.md
├── README.md
│
├── backend/
│   ├── pyproject.toml              # uv project config
│   ├── uv.lock
│   ├── .python-version
│   │
│   ├── src/
│   │   └── llm_holdem/
│   │       ├── __init__.py
│   │       ├── main.py             # FastAPI app entry point
│   │       ├── config.py           # Settings, env vars, API keys
│   │       │
│   │       ├── api/
│   │       │   ├── __init__.py
│   │       │   ├── routes.py       # REST endpoints (lobby, history)
│   │       │   ├── websocket.py    # WebSocket handler
│   │       │   └── schemas.py      # API request/response Pydantic models
│   │       │
│   │       ├── game/
│   │       │   ├── __init__.py
│   │       │   ├── engine.py       # Core game loop / coordinator
│   │       │   ├── dealer.py       # Deck, shuffling, dealing
│   │       │   ├── betting.py      # Betting rounds, action validation
│   │       │   ├── pot.py          # Pot calculation, side pots
│   │       │   ├── evaluator.py    # Hand evaluation (wraps treys)
│   │       │   ├── blinds.py       # Blind structure & escalation
│   │       │   ├── tournament.py   # Tournament logic, elimination, standings
│   │       │   ├── turn.py         # Turn order management
│   │       │   ├── timer.py        # 30-second turn timer
│   │       │   └── state.py        # Game state models (Pydantic)
│   │       │
│   │       ├── agents/
│   │       │   ├── __init__.py
│   │       │   ├── registry.py     # Agent roster registry
│   │       │   ├── profiles.py     # Agent profile definitions (30+)
│   │       │   ├── action_agent.py # Pydantic AI agent for game decisions
│   │       │   ├── chat_agent.py   # Pydantic AI agent for reactive chat
│   │       │   ├── prompt.py       # Prompt building & validation
│   │       │   ├── context.py      # Context window management
│   │       │   └── schemas.py      # Action/Chat response Pydantic models
│   │       │
│   │       ├── db/
│   │       │   ├── __init__.py
│   │       │   ├── database.py     # SQLite connection, engine setup
│   │       │   ├── models.py       # SQLModel table definitions
│   │       │   └── repository.py   # Data access layer (CRUD operations)
│   │       │
│   │       └── logging_config.py   # Structured logging + Logfire setup
│   │
│   └── tests/
│       ├── conftest.py
│       ├── test_game/
│       │   ├── test_engine.py
│       │   ├── test_dealer.py
│       │   ├── test_betting.py
│       │   ├── test_pot.py
│       │   ├── test_evaluator.py
│       │   ├── test_blinds.py
│       │   ├── test_tournament.py
│       │   ├── test_turn.py
│       │   └── test_timer.py
│       ├── test_agents/
│       │   ├── test_registry.py
│       │   ├── test_action_agent.py
│       │   ├── test_chat_agent.py
│       │   ├── test_prompt.py
│       │   └── test_context.py
│       ├── test_api/
│       │   ├── test_routes.py
│       │   └── test_websocket.py
│       └── test_db/
│           ├── test_models.py
│           └── test_repository.py
│
├── frontend/
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   │
│   ├── public/
│   │   └── avatars/                # Pre-made avatar images
│   │       ├── you.png             # Default human player avatar
│   │       ├── poker-pete.png
│   │       ├── bluffing-betty.png
│   │       └── ...                 # 30+ agent avatars
│   │
│   └── src/
│       ├── main.tsx                # App entry point
│       ├── App.tsx                 # Root component, routing
│       ├── App.css                 # Global styles
│       │
│       ├── types/
│       │   ├── game.ts             # Game state types (mirrors backend Pydantic models)
│       │   ├── messages.ts         # WebSocket message types
│       │   ├── agents.ts           # Agent profile types
│       │   └── api.ts              # REST API types
│       │
│       ├── stores/
│       │   ├── gameStore.ts        # Zustand store for game state
│       │   ├── lobbyStore.ts       # Zustand store for lobby state
│       │   └── chatStore.ts        # Zustand store for chat/action log
│       │
│       ├── hooks/
│       │   ├── useWebSocket.ts     # WebSocket connection management
│       │   ├── useGameActions.ts   # Player action helpers
│       │   └── useTimer.ts         # Turn timer hook
│       │
│       ├── pages/
│       │   ├── Lobby/
│       │   │   ├── Lobby.tsx
│       │   │   ├── Lobby.css
│       │   │   ├── NewGame.tsx
│       │   │   ├── InProgressGames.tsx
│       │   │   └── GameHistory.tsx
│       │   ├── GameTable/
│       │   │   ├── GameTable.tsx
│       │   │   └── GameTable.css
│       │   ├── PostGame/
│       │   │   ├── PostGame.tsx
│       │   │   └── PostGame.css
│       │   └── GameReview/
│       │       ├── GameReview.tsx
│       │       └── GameReview.css
│       │
│       ├── components/
│       │   ├── table/
│       │   │   ├── PokerTable.tsx       # Oval table with seats
│       │   │   ├── PokerTable.css
│       │   │   ├── PlayerSeat.tsx       # Individual player seat
│       │   │   ├── PlayerSeat.css
│       │   │   ├── CommunityCards.tsx   # Flop/turn/river display
│       │   │   ├── PotDisplay.tsx       # Main pot + side pots
│       │   │   └── DealerButton.tsx     # Dealer button indicator
│       │   ├── cards/
│       │   │   ├── Card.tsx             # Single card component
│       │   │   ├── Card.css
│       │   │   ├── CardBack.tsx         # Face-down card
│       │   │   └── HoleCards.tsx        # Two-card hole card display
│       │   ├── controls/
│       │   │   ├── ActionButtons.tsx    # Fold/Check/Call/Raise buttons
│       │   │   ├── ActionButtons.css
│       │   │   ├── RaiseSlider.tsx      # Raise amount slider
│       │   │   └── PresetButtons.tsx    # Min/2x/3x/Pot/All-In
│       │   ├── chat/
│       │   │   ├── ChatPanel.tsx        # Combined chat + action log
│       │   │   ├── ChatPanel.css
│       │   │   ├── ChatMessage.tsx      # Individual message display
│       │   │   └── ChatInput.tsx        # Human chat input
│       │   ├── avatars/
│       │   │   ├── Avatar.tsx           # Avatar with state indicators
│       │   │   └── Avatar.css
│       │   ├── timer/
│       │   │   ├── TurnTimer.tsx        # Countdown timer display
│       │   │   └── TurnTimer.css
│       │   ├── animations/
│       │   │   ├── DealAnimation.tsx    # Card dealing animation
│       │   │   ├── ChipAnimation.tsx    # Chip movement animation
│       │   │   ├── ShowdownAnimation.tsx # Tiered showdown effects
│       │   │   └── FoldAnimation.tsx    # Card fold animation
│       │   ├── lobby/
│       │   │   ├── AgentCard.tsx        # Agent roster card (name, avatar, bio)
│       │   │   ├── AgentCard.css
│       │   │   ├── SeatConfigurator.tsx # Per-seat agent picker
│       │   │   └── GameModeSelector.tsx # Play vs. Spectate toggle
│       │   └── common/
│       │       ├── CostIndicator.tsx    # API cost display
│       │       └── HandEvaluation.tsx   # Hand rank text display
│       │
│       └── services/
│           ├── websocket.ts        # WebSocket client service
│           └── api.ts              # REST API client service
│
└── pydantic-ai-documentation.md    # Reference documentation
```

---

## Backend Architecture

### Layer Overview

The backend follows a **layered architecture** with clear separation of concerns:

1. **API Layer** — HTTP/WebSocket interface
2. **Game Engine Layer** — Core poker logic (no LLM dependency)
3. **AI Agent Layer** — LLM interaction via Pydantic AI
4. **Data Layer** — Persistence via SQLModel/SQLite

### API Layer

#### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/agents` | List available agents (filtered by configured API keys) |
| `GET` | `/api/agents/{id}` | Get agent profile details |
| `GET` | `/api/games` | List all games (in-progress + completed) |
| `GET` | `/api/games/{id}` | Get game details and summary |
| `GET` | `/api/games/{id}/hands` | Get hand history for a game |
| `GET` | `/api/games/{id}/hands/{hand_num}` | Get specific hand replay data |
| `POST` | `/api/games` | Create a new game |
| `GET` | `/api/config/providers` | List which LLM providers are configured |
| `GET` | `/api/costs` | Get cumulative API cost data |

#### WebSocket Protocol

A single WebSocket connection at `/ws/game/{game_id}` carries all real-time communication.

**Server → Client Messages:**

| Message Type | Description |
|-------------|-------------|
| `game_state` | Full game state update (sent after every state change) |
| `chat_message` | AI or system chat message |
| `timer_update` | Turn timer tick |
| `game_over` | Tournament ended, includes final standings |
| `error` | Error notification |
| `game_paused` | Game paused (e.g., reconnection scenario) |
| `game_resumed` | Game resumed |

**Client → Server Messages:**

| Message Type | Description |
|-------------|-------------|
| `player_action` | Human player's action (fold/check/call/raise + amount) |
| `chat_message` | Human player's chat message |
| `pause_game` | Request to pause |

### Game Engine Layer

The game engine is a **pure logic layer** with no LLM or network dependencies. It can be fully tested in isolation.

#### Game Loop (Simplified)

```
Tournament Start
│
├── While (players_remaining > 1):
│   │
│   ├── Start New Hand
│   │   ├── Move dealer button
│   │   ├── Post blinds
│   │   ├── Shuffle & deal hole cards
│   │   └── Broadcast state
│   │
│   ├── Pre-Flop Betting Round
│   │   └── For each active player (in turn order):
│   │       ├── If AI: Request action from Action Agent
│   │       ├── If Human: Wait for WebSocket message (30s timer)
│   │       ├── Validate action
│   │       ├── Apply action to game state
│   │       ├── Trigger reactive chat (if key event)
│   │       └── Broadcast state
│   │
│   ├── Flop → Deal 3 community cards → Betting Round
│   ├── Turn → Deal 1 community card → Betting Round
│   ├── River → Deal 1 community card → Betting Round
│   │
│   ├── Showdown (if 2+ players remain)
│   │   ├── Evaluate hands
│   │   ├── Determine winner(s)
│   │   ├── Distribute pot(s) including side pots
│   │   ├── Trigger showdown chat reactions
│   │   └── Broadcast state with hand evaluation + animation tier
│   │
│   ├── Eliminate busted players
│   ├── Check blind escalation (every 10 hands)
│   └── Persist hand to database
│
├── Tournament Complete
│   ├── Record final standings
│   ├── Calculate summary stats
│   └── Broadcast game_over
```

#### Key Game State Model

```python
class GameState(BaseModel):
    game_id: str
    mode: Literal["player", "spectator"]
    status: Literal["waiting", "active", "paused", "completed"]

    # Table
    players: list[PlayerState]
    dealer_position: int
    small_blind: int
    big_blind: int
    hand_number: int

    # Current Hand
    community_cards: list[Card]
    pots: list[Pot]              # Main pot + side pots
    current_bet: int
    current_player_index: int | None
    phase: Literal["pre_flop", "flop", "turn", "river", "showdown", "between_hands"]

    # History
    current_hand_actions: list[Action]

class PlayerState(BaseModel):
    seat_index: int
    agent_id: str | None         # None for human player
    name: str
    avatar_url: str
    chips: int
    hole_cards: list[Card] | None  # None if hidden from viewer
    is_folded: bool
    is_eliminated: bool
    is_all_in: bool
    current_bet: int

class Card(BaseModel):
    rank: str                    # "2"-"9", "T", "J", "Q", "K", "A"
    suit: str                    # "h", "d", "c", "s"

class Pot(BaseModel):
    amount: int
    eligible_players: list[int]  # Seat indices

class Action(BaseModel):
    player_index: int
    action_type: Literal["fold", "check", "call", "raise", "post_blind"]
    amount: int | None
    timestamp: str
```

### AI Agent Layer

#### Agent Architecture

Two separate Pydantic AI agents handle different responsibilities:

**1. Action Agent** — Makes game decisions

```python
# Structured output model
class PokerAction(BaseModel):
    action: Literal["fold", "check", "call", "raise"]
    amount: int | None = None    # Required only for "raise"
    reasoning: str               # Internal reasoning (not shown to players, useful for debugging)
```

- Receives sanitized game state (own cards only, no opponents' hole cards)
- System prompt encodes agent personality and play style
- Returns structured `PokerAction` via Pydantic AI
- On invalid action: retry with error explanation, fallback to check/fold

**2. Chat Agent** — Produces reactive table talk

```python
class ChatResponse(BaseModel):
    message: str | None = None   # None = agent chooses not to speak
```

- Triggered after key events (all-ins, showdowns, eliminations, big pots, human chat)
- Receives recent game context + chat history
- System prompt encodes agent personality and table-talk style
- Not every agent responds to every event — controlled by personality traits + randomness

#### Prompt Builder & Validator

```
┌─────────────────────────────────────────┐
│           Prompt Builder                 │
│                                         │
│  1. Load agent system prompt            │
│  2. Build structured game context       │
│  3. Include hand history (truncated     │
│     if near context limit)              │
│  4. Include recent chat                 │
│                                         │
│         ┌──────────────┐                │
│         │  VALIDATOR   │                │
│         │              │                │
│         │  ✓ No opponent hole cards     │
│         │  ✓ No hidden information      │
│         │  ✓ Context within limits      │
│         │  ✓ Valid game state only      │
│         └──────────────┘                │
│                                         │
│  5. Send to Pydantic AI agent           │
└─────────────────────────────────────────┘
```

The validator is a **hard gate** — if validation fails, the prompt is rejected and an error is raised. This ensures information integrity is never compromised.

#### Context Window Manager

- Maintains a registry of model context window sizes
- Before each LLM call, estimates token count of the full prompt
- If exceeding the model's limit, truncates oldest hand history entries first
- Current hand + recent history always preserved
- Logs when truncation occurs for debugging

#### Agent Registry

```python
class AgentProfile(BaseModel):
    id: str                      # Unique agent ID
    name: str                    # Display name
    avatar: str                  # Filename in /avatars/
    backstory: str               # Flavor text / bio
    model: str                   # Pydantic AI model string (e.g., "openai:gpt-4o")
    provider: str                # Provider key (e.g., "openai", "anthropic")

    # Personality dimensions
    play_style: str              # e.g., "aggressive", "tight", "loose", "mathematical"
    talk_style: str              # e.g., "trash-talker", "silent", "friendly", "sarcastic"
    risk_tolerance: str          # e.g., "reckless", "calculated", "cautious"
    bluffing_tendency: str       # e.g., "frequent", "honest", "deceptive"

    # System prompts (generated from personality)
    action_system_prompt: str
    chat_system_prompt: str
```

The registry loads all 30+ agent profiles at startup, filters out agents whose provider API key is not configured, and exposes the available roster to the frontend.

### Data Layer

#### SQLModel Schema

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│    Game      │     │     GamePlayer   │     │    Hand      │
├──────────────┤     ├──────────────────┤     ├──────────────┤
│ id (PK)      │◄────│ game_id (FK)     │     │ id (PK)      │
│ mode         │     │ seat_index       │     │ game_id (FK) │◄──┐
│ status       │     │ agent_id (null   │     │ hand_number  │   │
│ created_at   │     │   for human)     │     │ dealer_pos   │   │
│ finished_at  │     │ name             │     │ small_blind  │   │
│ winner_seat  │     │ avatar           │     │ big_blind    │   │
│ total_hands  │     │ starting_chips   │     │ community    │   │
│ config_json  │     │ final_chips      │     │ pots_json    │   │
│              │     │ finish_position  │     │ winners_json │   │
│              │     │ elimination_hand │     │ phase        │   │
└──────────────┘     └──────────────────┘     └──────┬───────┘   │
                                                      │           │
                     ┌──────────────────┐             │           │
                     │   HandAction     │◄────────────┘           │
                     ├──────────────────┤                         │
                     │ id (PK)          │     ┌──────────────┐    │
                     │ hand_id (FK)     │     │  ChatMessage │    │
                     │ seat_index       │     ├──────────────┤    │
                     │ action_type      │     │ id (PK)      │    │
                     │ amount           │     │ game_id (FK) │────┘
                     │ phase            │     │ hand_number  │
                     │ sequence         │     │ seat_index   │
                     │ timestamp        │     │ message      │
                     └──────────────────┘     │ timestamp    │
                                              │ trigger_event│
                     ┌──────────────────┐     └──────────────┘
                     │   CostRecord     │
                     ├──────────────────┤
                     │ id (PK)          │
                     │ game_id (FK)     │
                     │ agent_id         │
                     │ call_type        │  ("action" | "chat")
                     │ model            │
                     │ input_tokens     │
                     │ output_tokens    │
                     │ estimated_cost   │
                     │ timestamp        │
                     └──────────────────┘
```

Tables are auto-created on startup via `SQLModel.metadata.create_all()`.

---

## Frontend Architecture

### Component Hierarchy

```
App
├── Lobby (page)
│   ├── GameModeSelector
│   ├── NewGame
│   │   ├── SeatConfigurator (×6)
│   │   │   └── AgentCard (roster browser)
│   │   └── StartGameButton
│   ├── InProgressGames
│   │   └── GameCard (resume button)
│   └── GameHistory
│       └── GameCard (review button)
│
├── GameTable (page)
│   ├── PokerTable
│   │   ├── PlayerSeat (×2-6)
│   │   │   ├── Avatar (with state: active/folded/low/thinking/eliminated)
│   │   │   ├── HoleCards (visible or CardBack)
│   │   │   ├── ChipCount
│   │   │   └── TurnTimer (when active)
│   │   ├── CommunityCards
│   │   ├── PotDisplay
│   │   └── DealerButton
│   ├── ActionButtons (player mode, when human's turn)
│   │   ├── FoldButton
│   │   ├── CheckCallButton
│   │   ├── PresetButtons (Min/2x/3x/Pot/All-In)
│   │   └── RaiseSlider
│   ├── ChatPanel
│   │   ├── ChatMessage (×n, scrollable)
│   │   └── ChatInput (player mode only)
│   ├── CostIndicator
│   └── Animations (overlay layer)
│       ├── DealAnimation
│       ├── ChipAnimation
│       ├── ShowdownAnimation
│       └── FoldAnimation
│
├── PostGame (page)
│   ├── FinalStandings
│   ├── GameStats
│   ├── RematchButton
│   └── BackToLobbyButton
│
└── GameReview (page)
    ├── PokerTable (replay state)
    ├── HandNavigator (prev/next hand)
    ├── ActionStepper (step through each action)
    └── ChatPanel (read-only, showing historical messages)
```

### Zustand Stores

**gameStore** — Primary game state from WebSocket

```typescript
interface GameStore {
  gameState: GameState | null;
  isConnected: boolean;
  setGameState: (state: GameState) => void;
  // Derived selectors
  currentPlayer: PlayerState | null;
  humanPlayer: PlayerState | null;
  isHumanTurn: boolean;
}
```

**lobbyStore** — Lobby and configuration state

```typescript
interface LobbyStore {
  agents: AgentProfile[];
  games: GameSummary[];
  inProgressGames: GameSummary[];
  selectedMode: "player" | "spectator";
  seatConfig: (string | "random" | null)[];  // agent IDs per seat
  fetchAgents: () => Promise<void>;
  fetchGames: () => Promise<void>;
}
```

**chatStore** — Chat and action log

```typescript
interface ChatStore {
  messages: ChatMessage[];
  addMessage: (msg: ChatMessage) => void;
  clearMessages: () => void;
}
```

### WebSocket Connection Management

- WebSocket connection established when entering the Game Table page
- Automatic reconnection with exponential backoff on disconnect
- On reconnect, backend sends full game state to resync
- Connection state reflected in UI (connected/reconnecting indicator)
- Game pauses server-side when WebSocket disconnects; resumes on reconnect

---

## WebSocket Message Protocol

### Type Definitions (Shared Concepts)

All messages are JSON with a `type` discriminator field.

**Server → Client:**

```typescript
type ServerMessage =
  | { type: "game_state"; data: GameState }
  | { type: "chat_message"; data: ChatMessageData }
  | { type: "timer_update"; data: { seat_index: number; seconds_remaining: number } }
  | { type: "game_over"; data: { standings: FinalStanding[]; stats: GameStats } }
  | { type: "error"; data: { message: string; code: string } }
  | { type: "game_paused"; data: { reason: string } }
  | { type: "game_resumed"; data: {} };
```

**Client → Server:**

```typescript
type ClientMessage =
  | { type: "player_action"; data: { action: "fold" | "check" | "call" | "raise"; amount?: number } }
  | { type: "chat_message"; data: { message: string } };
```

---

## Security & Information Integrity

### Prompt Validation Pipeline

Every LLM call passes through a validation pipeline:

```
Game State → Prompt Builder → ┌─────────────┐ → Pydantic AI Agent → LLM
                               │  Validator   │
                               │              │
                               │  1. Strip all│
                               │     opponent │
                               │     hole     │
                               │     cards    │
                               │              │
                               │  2. Verify   │
                               │     only     │
                               │     public   │
                               │     info +   │
                               │     own cards│
                               │              │
                               │  3. Check no │
                               │     hidden   │
                               │     state    │
                               │     leaked   │
                               └─────────────┘
```

The validator:
- Receives the complete game state and the target agent's seat index
- Builds a **sanitized view** containing only information visible to that agent
- Explicitly asserts no opponent hole cards are present
- Runs as a mandatory step — cannot be bypassed
- Logs validation passes/failures for auditing

### Session Enforcement

- Backend tracks active WebSocket connection
- Only one WebSocket connection allowed at a time
- Second connection attempt either rejects or replaces the first (TBD, likely reject)

---

## Error Handling Strategy

### LLM API Calls

```
LLM Call Attempt
├── Success → Parse structured output → Validate action → Apply
├── Failure (network/rate limit/500)
│   ├── Retry 1 (1s backoff)
│   ├── Retry 2 (2s backoff)
│   ├── Retry 3 (4s backoff)
│   └── All retries failed → Auto-fold for the hand
├── Invalid Action Response
│   ├── Retry with error explanation
│   └── Second invalid → Auto-check or auto-fold
└── Timeout (30s total timer)
    └── Auto-check or auto-fold
```

### WebSocket Disconnection

```
WebSocket Disconnect Detected
├── Server: Pause game loop immediately
├── Server: Persist current state to SQLite
├── Client: Show "Reconnecting..." overlay
├── Client: Attempt reconnection with exponential backoff
└── On Reconnect:
    ├── Server: Send full game state
    ├── Server: Resume game loop
    └── Client: Restore UI from received state
```

---

## Configuration

### Environment Variables

```bash
# LLM Provider API Keys (set the ones you want to use)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
GROQ_API_KEY=gsk_...
MISTRAL_API_KEY=...

# Optional: Ollama (local models, no key needed)
OLLAMA_BASE_URL=http://localhost:11434

# Pydantic Logfire (optional)
LOGFIRE_TOKEN=...

# Application
DATABASE_URL=sqlite:///./llm_holdem.db
LOG_LEVEL=INFO
```

### Agent Profile Configuration

Agent profiles are defined in Python as a list of `AgentProfile` objects in `backend/src/llm_holdem/agents/profiles.py`. Each profile specifies:
- The model string (e.g., `"openai:gpt-4o"`, `"anthropic:claude-sonnet-4-5"`)
- The provider key (used to check if the API key is configured)
- Personality traits and system prompts

This makes it easy to add, modify, or remove agents without changing any other code.
