import { useState, useEffect } from "react";
import { streamChat } from "../api";
import type { ChatMessage, ChatSession } from "../types";
import { MessageList } from "./MessageList";
import { Sidebar } from "./Sidebar";

export function Chat() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>("");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // Create a fresh chat on first mount
  useEffect(() => {
    createNewChat();
  }, []);

  const currentSession =
    sessions.find((s) => s.id === currentSessionId) ?? sessions[0];

  function createNewChat() {
    const newSession: ChatSession = {
      id: Math.random().toString(36).substring(2, 15),
      title: "New Chat",
      messages: [],
      createdAt: Date.now(),
    };

    setSessions((prev) => [newSession, ...prev]);
    setCurrentSessionId(newSession.id);
  }

  function deleteChat(id: string) {
    setSessions((prev) => {
      const filtered = prev.filter((s) => s.id !== id);

      if (id === currentSessionId) {
        if (filtered.length > 0) {
          setCurrentSessionId(filtered[0].id);
        } else {
          // If all chats are deleted, immediately create a new one
          const newSession: ChatSession = {
            id: Math.random().toString(36).substring(2, 15),
            title: "New Chat",
            messages: [],
            createdAt: Date.now(),
          };
          setCurrentSessionId(newSession.id);
          return [newSession];
        }
      }

      return filtered;
    });
  }

  async function send() {
    if (!input.trim() || !currentSession || loading) return;

    const trimmedInput = input.trim();
    const userMsg: ChatMessage = { role: "user", content: trimmedInput };

    setInput("");
    setLoading(true);

    // Append user message
    setSessions((prev) =>
      prev.map((s) =>
        s.id === currentSession.id
          ? {
              ...s,
              messages: [...s.messages, userMsg],
              title:
                s.messages.length === 0
                  ? trimmedInput.slice(0, 50) +
                    (trimmedInput.length > 50 ? "..." : "")
                  : s.title,
            }
          : s
      )
    );

    // Create assistant placeholder
    const assistantMsg: ChatMessage = {
      role: "assistant",
      content: "",
    };

    setSessions((prev) =>
      prev.map((s) =>
        s.id === currentSession.id
          ? { ...s, messages: [...s.messages, assistantMsg] }
          : s
      )
    );

    // Stream response
    await streamChat(currentSession.id, trimmedInput, (token) => {
      setSessions((prev) =>
        prev.map((s) => {
          if (s.id !== currentSession.id) return s;

          const msgs = [...s.messages];
          const last = msgs[msgs.length - 1];

          if (last?.role === "assistant") {
            msgs[msgs.length - 1] = {
              ...last,
              content: last.content + token,
            };
          }

          return { ...s, messages: msgs };
        })
      );
    });

    setLoading(false);
  }

  return (
    <div className="chat-container">
      <Sidebar
        sessions={sessions}
        currentSessionId={currentSession?.id ?? ""}
        onSelectSession={setCurrentSessionId}
        onNewChat={createNewChat}
        onDeleteChat={deleteChat}
      />

      <div className="chat">
        <MessageList messages={currentSession?.messages ?? []} />

        <div className="input-row">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) send();
            }}
            placeholder="Execute query..."
            disabled={loading}
          />

          <button onClick={send} disabled={loading}>
            {loading ? "PROCESSING" : "EXECUTE"}
          </button>
        </div>
      </div>
    </div>
  );
}
