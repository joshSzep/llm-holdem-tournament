/**
 * ChatMessage — a single chat entry (agent message or system event).
 */

interface ChatMessageProps {
  name: string;
  message: string;
  timestamp: string;
  isSystem: boolean;
}

export function ChatMessage({
  name,
  message,
  timestamp,
  isSystem,
}: ChatMessageProps): React.ReactElement {
  const time = new Date(timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  if (isSystem) {
    return (
      <div className="chat-message chat-message--system">
        <span className="chat-message__time">{time}</span>
        <span className="chat-message__text">{message}</span>
      </div>
    );
  }

  return (
    <div className="chat-message">
      <span className="chat-message__time">{time}</span>
      <span className="chat-message__name">{name}</span>
      <span className="chat-message__text">{message}</span>
    </div>
  );
}
