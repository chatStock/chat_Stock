import type { ChatMessage } from "../types";
import { Message } from "./Message";

export function MessageList({ messages }: { messages: ChatMessage[] }) {
  return (
    <div className="messages">
      {messages.map((m, i) => (
        <Message key={i} message={m} />
      ))}
    </div>
  );
}