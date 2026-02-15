/**
 * Tests for ChatMessage, ChatInput, and ChatPanel components.
 */

import { render, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { ChatMessage } from "../../components/chat/ChatMessage";
import { ChatInput } from "../../components/chat/ChatInput";
import { ChatPanel } from "../../components/chat/ChatPanel";
import { useChatStore } from "../../stores/chatStore";

// ─── ChatMessage ─────────────────────────────────────

describe("ChatMessage", () => {
  it("renders user message with name and text", () => {
    const { container } = render(
      <ChatMessage
        name="Alice"
        message="Hello!"
        timestamp="2024-01-01T12:00:00Z"
        isSystem={false}
      />,
    );
    expect(container.querySelector(".chat-message__name")).toHaveTextContent(
      "Alice",
    );
    expect(container.querySelector(".chat-message__text")).toHaveTextContent(
      "Hello!",
    );
  });

  it("renders system message without name", () => {
    const { container } = render(
      <ChatMessage
        name=""
        message="Game started"
        timestamp="2024-01-01T12:00:00Z"
        isSystem
      />,
    );
    expect(container.querySelector(".chat-message")).toHaveClass(
      "chat-message--system",
    );
    expect(
      container.querySelector(".chat-message__name"),
    ).not.toBeInTheDocument();
  });

  it("renders timestamp", () => {
    const { container } = render(
      <ChatMessage
        name="Bot"
        message="Hi"
        timestamp="2024-01-01T12:30:00Z"
        isSystem={false}
      />,
    );
    expect(container.querySelector(".chat-message__time")).toBeInTheDocument();
  });
});

// ─── ChatInput ───────────────────────────────────────

describe("ChatInput", () => {
  it("renders input field and send button", () => {
    const { container } = render(<ChatInput onSend={vi.fn()} />);
    expect(container.querySelector(".chat-input__field")).toBeInTheDocument();
    expect(container.querySelector(".chat-input__send")).toBeInTheDocument();
  });

  it("calls onSend with trimmed text on submit", () => {
    const onSend = vi.fn();
    const { container } = render(<ChatInput onSend={onSend} />);
    const input = container.querySelector(
      ".chat-input__field",
    ) as HTMLInputElement;
    const form = container.querySelector(".chat-input") as HTMLFormElement;

    fireEvent.change(input, { target: { value: "  Hello!  " } });
    fireEvent.submit(form);

    expect(onSend).toHaveBeenCalledWith("Hello!");
  });

  it("clears input after sending", () => {
    const onSend = vi.fn();
    const { container } = render(<ChatInput onSend={onSend} />);
    const input = container.querySelector(
      ".chat-input__field",
    ) as HTMLInputElement;
    const form = container.querySelector(".chat-input") as HTMLFormElement;

    fireEvent.change(input, { target: { value: "Test" } });
    fireEvent.submit(form);

    expect(input.value).toBe("");
  });

  it("does not send empty messages", () => {
    const onSend = vi.fn();
    const { container } = render(<ChatInput onSend={onSend} />);
    const form = container.querySelector(".chat-input") as HTMLFormElement;
    fireEvent.submit(form);
    expect(onSend).not.toHaveBeenCalled();
  });

  it("does not send whitespace-only messages", () => {
    const onSend = vi.fn();
    const { container } = render(<ChatInput onSend={onSend} />);
    const input = container.querySelector(
      ".chat-input__field",
    ) as HTMLInputElement;
    const form = container.querySelector(".chat-input") as HTMLFormElement;

    fireEvent.change(input, { target: { value: "   " } });
    fireEvent.submit(form);

    expect(onSend).not.toHaveBeenCalled();
  });

  it("disables input and button when disabled", () => {
    const { container } = render(<ChatInput onSend={vi.fn()} disabled />);
    expect(container.querySelector(".chat-input__field")).toBeDisabled();
    expect(container.querySelector(".chat-input__send")).toBeDisabled();
  });
});

// ─── ChatPanel ───────────────────────────────────────

describe("ChatPanel", () => {
  beforeEach(() => {
    useChatStore.getState().clearMessages();
  });

  it("shows empty message when no messages", () => {
    const { container } = render(
      <ChatPanel showInput={false} onSendChat={vi.fn()} />,
    );
    expect(container.querySelector(".chat-panel__empty")).toHaveTextContent(
      "No messages yet",
    );
  });

  it("shows messages from store", () => {
    useChatStore.getState().addMessage({
      id: "1",
      seat_index: 0,
      name: "Alice",
      message: "Hi there",
      timestamp: "2024-01-01T12:00:00Z",
      isSystem: false,
    });

    const { container } = render(
      <ChatPanel showInput={false} onSendChat={vi.fn()} />,
    );
    expect(container.querySelector(".chat-message__text")).toHaveTextContent(
      "Hi there",
    );
  });

  it("shows message count", () => {
    useChatStore.getState().addMessage({
      id: "1",
      seat_index: 0,
      name: "Alice",
      message: "Hello",
      timestamp: "2024-01-01T12:00:00Z",
      isSystem: false,
    });
    useChatStore.getState().addMessage({
      id: "2",
      seat_index: 1,
      name: "Bob",
      message: "Hi",
      timestamp: "2024-01-01T12:00:01Z",
      isSystem: false,
    });

    const { container } = render(
      <ChatPanel showInput={false} onSendChat={vi.fn()} />,
    );
    expect(container.querySelector(".chat-panel__count")).toHaveTextContent(
      "2",
    );
  });

  it("shows input when showInput is true", () => {
    const { container } = render(
      <ChatPanel showInput onSendChat={vi.fn()} />,
    );
    expect(container.querySelector(".chat-input")).toBeInTheDocument();
  });

  it("hides input when showInput is false", () => {
    const { container } = render(
      <ChatPanel showInput={false} onSendChat={vi.fn()} />,
    );
    expect(container.querySelector(".chat-input")).not.toBeInTheDocument();
  });
});
