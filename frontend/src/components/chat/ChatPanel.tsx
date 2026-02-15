/**
 * ChatPanel — scrollable chat log with optional input.
 */

import { useRef, useEffect } from "react";
import "./ChatPanel.css";
import { useChatStore } from "../../stores/chatStore";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";

interface ChatPanelProps {
  showInput: boolean;
  onSendChat: (message: string) => void;
}

export function ChatPanel({
  showInput,
  onSendChat,
}: ChatPanelProps): React.ReactElement {
  const messages = useChatStore((s) => s.messages);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    const el = scrollRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="chat-panel">
      <div className="chat-panel__header">
        <h3 className="chat-panel__title">Chat</h3>
        <span className="chat-panel__count">{messages.length}</span>
      </div>

      <div className="chat-panel__messages" ref={scrollRef}>
        {messages.length === 0 ? (
          <div className="chat-panel__empty">No messages yet</div>
        ) : (
          messages.map((msg) => (
            <ChatMessage
              key={msg.id}
              name={msg.name}
              message={msg.message}
              timestamp={msg.timestamp}
              isSystem={msg.isSystem}
            />
          ))
        )}
      </div>

      {showInput && <ChatInput onSend={onSendChat} />}
    </div>
  );
}
