/**
 * ChatInput — text input for sending chat messages (player mode only).
 */

import { useState, useCallback } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({
  onSend,
  disabled = false,
}: ChatInputProps): React.ReactElement {
  const [text, setText] = useState("");

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const trimmed = text.trim();
      if (trimmed.length === 0) return;
      onSend(trimmed);
      setText("");
    },
    [text, onSend],
  );

  return (
    <form className="chat-input" onSubmit={handleSubmit}>
      <input
        type="text"
        className="chat-input__field"
        placeholder="Say something…"
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={disabled}
        maxLength={200}
      />
      <button
        type="submit"
        className="chat-input__send"
        disabled={disabled || text.trim().length === 0}
      >
        Send
      </button>
    </form>
  );
}
