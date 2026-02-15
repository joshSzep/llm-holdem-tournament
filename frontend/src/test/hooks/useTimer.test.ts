/**
 * Tests for useTimer hook.
 */

import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { useTimer } from "../../hooks/useTimer";
import { useGameStore } from "../../stores/gameStore";

describe("useTimer", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    useGameStore.setState({ timer: null });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns inactive state when no server timer", () => {
    const { result } = renderHook(() => useTimer());

    expect(result.current.isActive).toBe(false);
    expect(result.current.seatIndex).toBeNull();
    expect(result.current.secondsRemaining).toBe(0);
    expect(result.current.isUrgent).toBe(false);
  });

  it("syncs with server timer", () => {
    useGameStore.setState({
      timer: { seat_index: 2, seconds_remaining: 30 },
    });

    const { result } = renderHook(() => useTimer());

    expect(result.current.isActive).toBe(true);
    expect(result.current.seatIndex).toBe(2);
    expect(result.current.secondsRemaining).toBe(30);
    expect(result.current.isUrgent).toBe(false);
  });

  it("counts down locally", () => {
    useGameStore.setState({
      timer: { seat_index: 1, seconds_remaining: 20 },
    });

    const { result } = renderHook(() => useTimer());
    expect(result.current.secondsRemaining).toBe(20);

    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(result.current.secondsRemaining).toBe(19);

    act(() => {
      vi.advanceTimersByTime(3000);
    });
    expect(result.current.secondsRemaining).toBe(16);
  });

  it("marks as urgent when <= 10 seconds", () => {
    useGameStore.setState({
      timer: { seat_index: 0, seconds_remaining: 11 },
    });

    const { result } = renderHook(() => useTimer());
    expect(result.current.isUrgent).toBe(false);

    act(() => {
      vi.advanceTimersByTime(2000);
    });
    expect(result.current.secondsRemaining).toBe(9);
    expect(result.current.isUrgent).toBe(true);
  });

  it("does not go below zero", () => {
    useGameStore.setState({
      timer: { seat_index: 0, seconds_remaining: 2 },
    });

    const { result } = renderHook(() => useTimer());

    act(() => {
      vi.advanceTimersByTime(5000);
    });
    expect(result.current.secondsRemaining).toBe(0);
  });

  it("resets when server timer cleared", () => {
    useGameStore.setState({
      timer: { seat_index: 0, seconds_remaining: 30 },
    });

    const { result, rerender } = renderHook(() => useTimer());
    expect(result.current.isActive).toBe(true);

    act(() => {
      useGameStore.setState({ timer: null });
    });
    rerender();

    expect(result.current.isActive).toBe(false);
    expect(result.current.secondsRemaining).toBe(0);
  });
});
