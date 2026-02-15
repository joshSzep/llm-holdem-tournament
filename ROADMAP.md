# LLM Hold'Em Tournament - Implementation Roadmap

## Overview

This roadmap breaks the project into **6 phases**, each building on the previous one. Each phase results in a working, testable milestone. Phases are further broken into discrete tasks that can be worked on sequentially.

---

## Phase 1: Project Foundation & Core Poker Engine

**Goal**: Set up the project infrastructure and build the core poker game engine with no LLM or UI dependencies. This is the bedrock — all game logic is built and thoroughly tested here.

### 1.1 Project Scaffolding
- [x] Initialize monorepo structure (`frontend/`, `backend/`)
- [x] Set up `backend/` with `uv` and `pyproject.toml`
  - Python 3.12+, FastAPI, SQLModel, pydantic-ai, treys, logfire
- [x] Set up `frontend/` with `pnpm` and Vite + React + TypeScript
  - Zustand, Framer Motion, ESLint, Prettier
- [x] Create `justfile` with initial commands:
  - `just dev` — start both frontend and backend
  - `just test` — run all tests
  - `just lint` — run all linters
  - `just format` — run all formatters
- [x] Set up `.pre-commit-config.yaml` with ruff, prettier, eslint hooks
- [x] Create `.env.example` with all environment variable templates
- [x] Set up backend structured logging + Logfire integration
- [x] Set up pytest with coverage enforcement (≥80%)
- [x] Set up vitest with coverage enforcement (≥80%)
- [x] Create `README.md` with setup instructions

### 1.2 Card & Deck Primitives
- [x] Implement `Card` model (rank + suit)
- [x] Implement `Deck` class (52 cards, shuffle, deal)
- [x] Write comprehensive tests for deck operations
  - Full deck integrity, no duplicates, proper shuffle randomness

### 1.3 Hand Evaluator
- [x] Integrate `treys` library for hand evaluation
- [x] Create `evaluator.py` wrapper with clean API
  - `evaluate_hand(hole_cards, community_cards) -> HandResult`
  - `HandResult` includes rank, rank name (e.g., "Full House, Kings full of Sevens"), comparison value
- [x] Implement hand comparison for determining winners
- [x] Write tests for all hand types (high card through royal flush)
- [x] Write tests for tie-breaking scenarios
- [x] Write tests for split pot hand comparisons

### 1.4 Pot Manager
- [x] Implement main pot tracking
- [x] Implement side pot calculation for all-in scenarios
  - Multiple all-ins at different stack sizes
- [x] Implement pot distribution to winners
- [x] Implement split pot distribution (odd chip rule)
- [x] Write extensive tests for complex pot scenarios

### 1.5 Blind Manager
- [x] Implement blind structure (doubling every 10 hands)
  - 10/20 → 20/40 → 40/80 → 75/150 → 150/300 → 300/600 → 500/1000 → 1000/2000
- [x] Implement blind posting logic
- [x] Implement blind escalation tracking (hand counter)
- [x] Write tests for blind progression and posting

### 1.6 Turn Manager
- [x] Implement turn order logic for all betting rounds
  - Pre-flop: left of big blind, wrapping around
  - Post-flop: left of dealer
- [x] Implement standard heads-up rules (dealer=SB, acts first pre-flop, last post-flop)
- [x] Handle skipping folded/all-in/eliminated players
- [x] Implement dealer button rotation
- [x] Write tests for all turn order scenarios (3-6 players, heads-up)

### 1.7 Betting Manager
- [x] Implement action validation
  - Valid actions based on current state (when can you check vs. must call, min raise, etc.)
- [x] Implement fold, check, call, raise/bet actions
  - Apply to game state, update pot, current bet, player bet
- [x] Implement all-in logic (partial calls, under-raises)
- [x] Implement betting round completion detection
- [x] Write tests for all action types and edge cases

### 1.8 Game Engine (Core Loop)
- [x] Implement `GameEngine` class that orchestrates a complete hand:
  - Dealer button, blinds, deal, betting rounds, showdown, pot distribution
- [x] Implement game state model (`GameState`, `PlayerState`, etc.)
- [x] Implement phase transitions (pre-flop → flop → turn → river → showdown)
- [x] Handle early hand endings (everyone folds to one player)
- [x] Handle showdown with hand evaluation and winner determination
- [x] Write integration tests for complete hands (various scenarios)

### 1.9 Tournament Manager
- [x] Implement player elimination (0 chips)
- [x] Implement tournament completion detection (1 player remaining)
- [x] Implement final standings tracking
- [x] Implement game statistics collection (biggest pot, best hand, etc.)
- [x] Write tests for tournament progression and edge cases

---

## Phase 2: Database, API & Session Management

**Goal**: Add persistence, REST API, and WebSocket infrastructure. The game engine can now create/save/resume games.

### 2.1 Database Setup
- [x] Implement SQLModel table models (`Game`, `GamePlayer`, `Hand`, `HandAction`, `ChatMessage`, `CostRecord`)
- [x] Implement auto-create tables on startup
- [x] Implement database connection management (async SQLite via aiosqlite)
- [x] Write tests for model creation and relationships

### 2.2 Data Repository
- [x] Implement CRUD operations for games (create, get, list, update status)
- [x] Implement game player management
- [x] Implement hand history persistence (save complete hand after each hand)
- [x] Implement action logging
- [x] Implement chat message persistence
- [x] Implement cost record persistence
- [x] Implement game statistics queries
- [x] Write tests for all repository operations

### 2.3 Game State Persistence
- [x] Implement save/restore game state to/from database
- [x] Ensure game engine can resume from persisted state
- [x] Write tests for save/resume round-trip

### 2.4 FastAPI Application Setup
- [x] Create FastAPI app with CORS configuration
- [x] Implement health check endpoint
- [x] Implement configuration endpoint (available providers)
- [x] Set up dependency injection for database sessions

### 2.5 REST API Endpoints
- [x] `GET /api/agents` — list available agents (stub data for now)
- [x] `GET /api/games` — list all games
- [x] `GET /api/games/{id}` — get game details
- [x] `GET /api/games/{id}/hands` — get hand history
- [x] `GET /api/games/{id}/hands/{num}` — get specific hand
- [x] `POST /api/games` — create new game
- [x] `GET /api/config/providers` — available providers
- [x] `GET /api/costs` — cost tracking data
- [x] Write tests for all endpoints

### 2.6 WebSocket Handler
- [x] Implement WebSocket connection at `/ws/game/{game_id}`
- [x] Implement session enforcement (one connection at a time)
- [x] Implement server→client message serialization (Pydantic → JSON)
- [x] Implement client→server message deserialization and validation
- [x] Implement game state broadcast on every state change
- [x] Implement connection/disconnection handling (pause/resume game)
- [x] Implement timer update broadcasts
- [x] Write tests for WebSocket communication

### 2.7 Turn Timer
- [x] Implement 30-second countdown timer per turn
- [x] Implement timer broadcasting to frontend
- [x] Implement auto-check/fold on timeout
- [x] Integrate timer with game engine loop
- [x] Write tests for timer behavior and timeout actions

### 2.8 Game Coordinator
- [x] Implement game coordinator that ties together:
  - Game engine + WebSocket handler + database persistence
- [x] Implement the async game loop:
  - For AI turns: placeholder (random action) for now
  - For human turns: wait for WebSocket message with timer
- [x] Implement pause/resume on WebSocket disconnect/reconnect
- [x] Write integration tests for the full flow

---

## Phase 3: AI Agent System

**Goal**: Integrate Pydantic AI to make AI opponents that actually play poker and talk. Replace placeholder random actions with real LLM decisions.

### 3.1 Agent Profile Definitions
- [ ] Design the agent profile schema (`AgentProfile` model)
- [ ] Create initial set of 30+ agent profiles with:
  - Unique names, backstory/flavor text
  - Model assignments across providers (OpenAI, Anthropic, Google, etc.)
  - Personality dimensions (play style, talk style, risk tolerance, bluffing)
- [ ] Create system prompt templates for action decisions
- [ ] Create system prompt templates for chat/table talk
- [ ] Write tests for profile loading and validation

### 3.2 Agent Registry
- [ ] Implement agent registry that loads all profiles
- [ ] Implement provider detection (check which API keys are configured)
- [ ] Filter roster to only include agents with available providers
- [ ] Expose filtered roster via REST API (`GET /api/agents`)
- [ ] Write tests for registry filtering logic

### 3.3 Prompt Builder
- [ ] Implement structured game context builder
  - Format hole cards, community cards, pot, stacks, betting history
- [ ] Implement hand history formatter
- [ ] Implement recent chat formatter
- [ ] Write tests for prompt building output

### 3.4 Prompt Validator (Information Integrity)
- [ ] Implement sanitized view builder (strip opponent hole cards)
- [ ] Implement validation assertions:
  - No opponent hole cards present
  - Only public information + agent's own cards
  - No hidden state leaked
- [ ] Make validator a mandatory gate before every LLM call
- [ ] Write thorough tests for validation (positive and negative cases)
  - Ensure validation catches intentional leaks in test fixtures

### 3.5 Context Window Manager
- [ ] Build model context window size registry
- [ ] Implement token estimation for prompts
- [ ] Implement oldest-first hand history truncation
- [ ] Ensure current hand + recent history always preserved
- [ ] Write tests for truncation behavior near various context limits

### 3.6 Action Agent (Game Decisions)
- [ ] Implement Pydantic AI agent for poker decisions
  - Input: sanitized game state + personality prompt
  - Output: structured `PokerAction` (action + amount + reasoning)
- [ ] Integrate with game engine (replace placeholder random actions)
- [ ] Implement invalid action retry logic
  - Send error explanation, re-ask LLM
  - Fallback to check/fold after retry failure
- [ ] Implement error handling with exponential backoff
  - Network errors, rate limits → retry
  - All retries failed → auto-fold
- [ ] Integrate with 30-second turn timer
- [ ] Write tests with mocked LLM responses

### 3.7 Chat Agent (Reactive Table Talk)
- [ ] Implement Pydantic AI agent for chat/table talk
  - Input: game event context + personality prompt
  - Output: structured `ChatResponse` (message or None)
- [ ] Implement event trigger system:
  - Define key events: all-in, showdown, elimination, big pot, human chat
  - After each trigger, select which agents get a chat opportunity
  - Personality + randomness controls who speaks
- [ ] Implement chat throttling (prevent spam)
- [ ] Integrate chat messages into WebSocket broadcast
- [ ] Persist chat messages to database
- [ ] Write tests with mocked LLM responses

### 3.8 Cost Tracking
- [ ] Capture token usage from Pydantic AI responses
- [ ] Estimate cost based on model pricing
- [ ] Persist cost records to database
- [ ] Implement cumulative cost calculation
- [ ] Expose cost data via REST API and WebSocket
- [ ] Write tests for cost tracking accuracy

---

## Phase 4: Frontend — Core UI

**Goal**: Build the entire frontend UI with real WebSocket integration. The game is fully playable end-to-end at this point.

### 4.1 App Shell & Routing
- [ ] Set up React Router for page navigation
  - `/` → Lobby
  - `/game/:id` → Game Table
  - `/game/:id/results` → Post-Game Summary
  - `/game/:id/review` → Game Review
- [ ] Create App shell with dark theme base styles
- [ ] Set up global CSS variables (colors, spacing, typography)
- [ ] Set up Zustand stores (game, lobby, chat)

### 4.2 WebSocket Service
- [ ] Implement WebSocket client service
  - Connect, disconnect, send messages
  - Auto-reconnect with exponential backoff
- [ ] Implement `useWebSocket` hook
  - Connection state management
  - Message dispatch to Zustand stores
- [ ] Implement typed message handling (discriminated union on `type`)
- [ ] Write tests for WebSocket service

### 4.3 REST API Service
- [ ] Implement API client service (fetch wrapper)
- [ ] Implement typed API calls for all endpoints
- [ ] Write tests for API service

### 4.4 Lobby Page
- [ ] Build lobby layout (New Game / In-Progress / History sections)
- [ ] Build Game Mode Selector (Play vs. Spectate toggle)
- [ ] Build Seat Configurator
  - Visual seat arrangement (2-6 seats)
  - Per-seat: choose agent from roster or "Random"
  - Agent roster browser with AgentCard (name, avatar, backstory)
- [ ] Build In-Progress Games list with Resume button
- [ ] Build Game History list with Review button
- [ ] Style with dark theme CSS
- [ ] Write component tests

### 4.5 Poker Table — Static Layout
- [ ] Build PokerTable component (oval table, bird's-eye view)
- [ ] Build PlayerSeat component (avatar, name, chip count, cards area)
  - Position seats dynamically around the table for 2-6 players
- [ ] Build CommunityCards component (5-card area in center)
- [ ] Build PotDisplay component (main pot + side pots)
- [ ] Build DealerButton component
- [ ] Style with dark theme CSS
- [ ] Write component tests

### 4.6 Card Components
- [ ] Build Card component (simple design, rank + suit display)
- [ ] Build CardBack component (face-down card)
- [ ] Build HoleCards component (two-card display per player)
- [ ] Handle visibility rules:
  - Player mode: own cards face-up, opponents face-down
  - Spectator mode: all cards face-up
- [ ] Style cards with clean, high-contrast design
- [ ] Write component tests

### 4.7 Player Controls
- [ ] Build ActionButtons component (Fold, Check, Call, Raise)
  - Context-aware labels (Check vs. Call, Bet vs. Raise)
  - Disabled when not human's turn
- [ ] Build PresetButtons (Min Raise, 2x, 3x, Pot, All-In)
- [ ] Build RaiseSlider (min raise to all-in range)
- [ ] Integrate with WebSocket to send player actions
- [ ] Implement `useGameActions` hook
- [ ] Style with dark theme CSS
- [ ] Write component tests

### 4.8 Chat Panel
- [ ] Build ChatPanel component (scrollable message list)
- [ ] Build ChatMessage component (distinguish chat vs. game action visually)
- [ ] Build ChatInput component (text input + send button)
  - Visible in Player mode only
  - Disabled in Spectator mode
- [ ] Integrate with WebSocket for sending/receiving chat
- [ ] Style with dark theme CSS
- [ ] Write component tests

### 4.9 Turn Timer
- [ ] Build TurnTimer component (visual countdown)
- [ ] Implement `useTimer` hook synchronized with server timer updates
- [ ] Display on active player's seat
- [ ] Visual urgency (color change as time runs low)
- [ ] Style with dark theme CSS
- [ ] Write component tests

### 4.10 Avatar Component
- [ ] Build Avatar component with state indicators:
  - Default, Active turn (glow), Folded (grey), Low chips (red border)
  - Thinking (spinning dots), Eliminated (dimmed)
- [ ] Bundle placeholder avatar images (can be refined later)
- [ ] Style with dark theme CSS
- [ ] Write component tests

### 4.11 Cost Indicator
- [ ] Build CostIndicator component
- [ ] Display current game cost and cumulative session cost
- [ ] Position unobtrusively in UI
- [ ] Write component tests

### 4.12 Integration — Full Game Flow
- [ ] Wire up lobby → create game → navigate to game table
- [ ] Wire up WebSocket connection on game table mount
- [ ] Wire up game state updates → Zustand → UI re-renders
- [ ] Wire up player actions → WebSocket → backend → state update
- [ ] Wire up chat messages end-to-end
- [ ] Wire up timer display
- [ ] Test complete game flow manually (end-to-end)

---

## Phase 5: Animations & Polish

**Goal**: Add all animations, showdown effects, and visual polish to make the game exciting and appealing.

### 5.1 Card Dealing Animation
- [ ] Animate cards from deck position to player seat positions
- [ ] Stagger dealing animation (one card at a time, round-robin)
- [ ] Animate community card reveals (flop: 3 cards, turn, river)
- [ ] Use Framer Motion for smooth transitions

### 5.2 Chip Animations
- [ ] Animate chip count moving from player to pot on bet/call/raise
- [ ] Animate pot distribution to winner at end of hand
- [ ] Animate blind posting
- [ ] Smooth number transitions for chip count changes

### 5.3 Player Action Animations
- [ ] Fold animation (cards sliding/fading away)
- [ ] Check animation (subtle tap indicator)
- [ ] Call/Raise animation (chip push + amount display)
- [ ] All-in animation (dramatic chip push)

### 5.4 Dealer Button Animation
- [ ] Smooth movement of dealer button between seats between hands

### 5.5 Showdown Animations (Tiered by Hand Strength)
- [ ] High Card / One Pair: minimal — simple card reveal
- [ ] Two Pair / Three of a Kind: subtle — slight glow or highlight
- [ ] Straight / Flush: moderate — expanding highlight with emphasis
- [ ] Full House: impressive — dramatic reveal with strong glow
- [ ] Four of a Kind / Straight Flush: very impressive — particles or light burst
- [ ] Royal Flush: most spectacular — full celebration animation
- [ ] Display hand evaluation text with animation (e.g., "Full House, Kings full of Sevens")

### 5.6 Player Elimination Animation
- [ ] Dramatic seat dimming/fading when a player is eliminated
- [ ] Brief "eliminated" banner or label

### 5.7 Transitions & Polish
- [ ] Page transition animations (lobby → table, table → results)
- [ ] Smooth game phase transitions
- [ ] Loading/connecting states with appropriate visuals
- [ ] Reconnection overlay animation
- [ ] General CSS polish pass (spacing, typography, hover states, focus states)

---

## Phase 6: Post-Game, Review & Final Features

**Goal**: Complete the post-game experience, game review system, and finalize all remaining features.

### 6.1 Post-Game Summary Screen
- [ ] Build PostGame page layout
- [ ] Display final standings with finishing positions
- [ ] Calculate and display game statistics:
  - Total hands played
  - Biggest pot
  - Best hand
  - Most aggressive player
  - Most hands won
  - Bluff count (if detectable from action patterns)
- [ ] Build Rematch button (create new game with same opponents)
- [ ] Build Back to Lobby button
- [ ] Style with dark theme
- [ ] Write component tests

### 6.2 Game Review / Replay System
- [ ] Build GameReview page layout
- [ ] Implement hand navigator (previous/next hand)
- [ ] Implement action stepper (step forward/backward through each action in a hand)
- [ ] Reconstruct table visual state at each step from persisted data
- [ ] Display all chat messages at their correct positions in the timeline
- [ ] Show all hole cards (review mode = omniscient view)
- [ ] Read-only — no actions or chat input
- [ ] Style with dark theme
- [ ] Write component tests

### 6.3 Avatar Assets
- [ ] Create or source 30+ distinct avatar images for the agent roster
- [ ] Create default "You" avatar for the human player
- [ ] Ensure all avatars work well at small sizes with state borders
- [ ] Optimize image sizes for web

### 6.4 Agent Roster Finalization
- [ ] Finalize all 30+ agent profiles:
  - Names, backstories, personality dimensions
  - Model assignments spread across providers
  - Fine-tune action system prompts per personality
  - Fine-tune chat system prompts per personality
- [ ] Balance roster across play styles, talk styles, and providers
- [ ] Playtest and iterate on agent prompt quality

### 6.5 End-to-End Testing
- [ ] Full game flow tests (lobby → game → post-game)
- [ ] Spectator mode full game test
- [ ] Game pause/resume test (disconnect/reconnect)
- [ ] Game review walkthrough test
- [ ] Side pot scenarios in a real game
- [ ] Heads-up final two players test
- [ ] All blind levels reached test (long game)
- [ ] Cost tracking accuracy validation
- [ ] Multiple games in sequence (create, play, review, create another)

### 6.6 Documentation & Cleanup
- [ ] Write comprehensive `README.md`:
  - Project overview
  - Prerequisites (Node.js, Python, API keys)
  - Setup instructions
  - How to run (development)
  - How to configure API keys
  - How to add custom agents
- [ ] Code cleanup pass (remove TODOs, dead code)
- [ ] Ensure all tests pass with ≥80% coverage
- [ ] Final lint/format pass

---

## Phase Summary

| Phase | Name | Key Deliverable |
|-------|------|----------------|
| **1** | Foundation & Poker Engine | Fully tested poker game engine (no UI, no LLM) |
| **2** | Database, API & Sessions | Backend API + WebSocket + persistence; game playable with random AI |
| **3** | AI Agent System | LLM-powered opponents with personalities and table talk |
| **4** | Frontend Core UI | Complete playable UI; end-to-end game works |
| **5** | Animations & Polish | All animations, showdown effects, visual polish |
| **6** | Post-Game, Review & Final | Game review, summary stats, avatar assets, final polish |

---

## Dependencies Between Phases

```
Phase 1 ─────► Phase 2 ─────► Phase 3
                  │                │
                  │                ▼
                  └──────► Phase 4 ◄── (needs API + WebSocket from Phase 2,
                              │          AI agents from Phase 3)
                              │
                              ▼
                          Phase 5 ──────► Phase 6
```

- **Phase 1** has no dependencies (pure logic)
- **Phase 2** depends on Phase 1 (game engine)
- **Phase 3** depends on Phase 2 (API layer for agent registry, database for persistence)
- **Phase 4** depends on Phase 2 (API + WebSocket) and Phase 3 (AI agents for gameplay)
  - *Note*: Phase 4 frontend layout work (4.1-4.6) can start in parallel with Phase 3 using mock data
- **Phase 5** depends on Phase 4 (UI components to animate)
- **Phase 6** depends on Phase 4 and Phase 5 (complete UI with animations)
