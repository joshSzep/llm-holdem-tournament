/**
 * Tests for useGameActions hook.
 */

import { renderHook } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { useGameActions } from "../../hooks/useGameActions";

describe("useGameActions", () => {
  it("sends fold action", () => {
    const send = vi.fn();
    const { result } = renderHook(() => useGameActions(send));
    result.current.fold();
    expect(send).toHaveBeenCalledWith({
      type: "player_action",
      action_type: "fold",
    });
  });

  it("sends check action", () => {
    const send = vi.fn();
    const { result } = renderHook(() => useGameActions(send));
    result.current.check();
    expect(send).toHaveBeenCalledWith({
      type: "player_action",
      action_type: "check",
    });
  });

  it("sends call action", () => {
    const send = vi.fn();
    const { result } = renderHook(() => useGameActions(send));
    result.current.call();
    expect(send).toHaveBeenCalledWith({
      type: "player_action",
      action_type: "call",
    });
  });

  it("sends raise action with amount", () => {
    const send = vi.fn();
    const { result } = renderHook(() => useGameActions(send));
    result.current.raise(200);
    expect(send).toHaveBeenCalledWith({
      type: "player_action",
      action_type: "raise",
      amount: 200,
    });
  });

  it("sends chat message", () => {
    const send = vi.fn();
    const { result } = renderHook(() => useGameActions(send));
    result.current.sendChat("Hello!");
    expect(send).toHaveBeenCalledWith({
      type: "chat_message",
      message: "Hello!",
    });
  });
});
