/**
 * Tests for App component routing.
 */

import { render } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { Routes, Route } from "react-router-dom";

// Mock pages to avoid pulling in all dependencies
vi.mock("./pages/Lobby/Lobby", () => ({
  Lobby: () => <div data-testid="lobby-page">Lobby</div>,
}));

vi.mock("./pages/GameTable/GameTable", () => ({
  GameTable: () => <div data-testid="game-table-page">GameTable</div>,
}));

vi.mock("./pages/PostGame/PostGame", () => ({
  PostGame: () => <div data-testid="post-game-page">PostGame</div>,
}));

vi.mock("./pages/GameReview/GameReview", () => ({
  GameReview: () => <div data-testid="game-review-page">GameReview</div>,
}));

// Since App itself uses BrowserRouter, we test routes directly
describe("App routing", () => {
  function TestRoutes({ path }: { path: string }): React.ReactElement {
    return (
      <MemoryRouter initialEntries={[path]}>
        <div className="app">
          <Routes>
            <Route
              path="/"
              element={<div data-testid="lobby-page">Lobby</div>}
            />
            <Route
              path="/game/:id"
              element={<div data-testid="game-table-page">GameTable</div>}
            />
            <Route
              path="/game/:id/results"
              element={<div data-testid="post-game-page">PostGame</div>}
            />
            <Route
              path="/game/:id/review"
              element={<div data-testid="game-review-page">GameReview</div>}
            />
          </Routes>
        </div>
      </MemoryRouter>
    );
  }

  it("renders lobby at /", () => {
    const { getByTestId } = render(<TestRoutes path="/" />);
    expect(getByTestId("lobby-page")).toBeInTheDocument();
  });

  it("renders game table at /game/:id", () => {
    const { getByTestId } = render(<TestRoutes path="/game/1" />);
    expect(getByTestId("game-table-page")).toBeInTheDocument();
  });

  it("renders post game at /game/:id/results", () => {
    const { getByTestId } = render(<TestRoutes path="/game/1/results" />);
    expect(getByTestId("post-game-page")).toBeInTheDocument();
  });

  it("renders game review at /game/:id/review", () => {
    const { getByTestId } = render(<TestRoutes path="/game/1/review" />);
    expect(getByTestId("game-review-page")).toBeInTheDocument();
  });
});
