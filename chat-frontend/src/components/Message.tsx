import type { ChatMessage } from "../types";

export function Message({ message }: { message: ChatMessage }) {
  return (
    <div className={`message ${message.role}`}>
      {message.content}
    </div>
  );
}