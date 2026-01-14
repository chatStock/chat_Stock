import type { ChatSession } from "../types";

interface SidebarProps {
  sessions: ChatSession[];
  currentSessionId: string;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onDeleteChat: (id: string) => void;
}

export function Sidebar({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewChat,
  onDeleteChat,
}: SidebarProps) {
  return (
    <div className="sidebar">
      <button className="new-chat-btn" onClick={onNewChat}>
        + NEW STRATEGY
      </button>
      
      <div className="session-list">
        {sessions.map((session) => (
          <div
            key={session.id}
            className={`session-item ${
              session.id === currentSessionId ? "active" : ""
            }`}
            onClick={() => onSelectSession(session.id)}
          >
            <div className="session-title">{session.title}</div>
            <button
              className="delete-btn"
              onClick={(e) => {
                e.stopPropagation();
                onDeleteChat(session.id);
              }}
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}