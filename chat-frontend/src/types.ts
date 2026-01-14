export type Role = "user" | "assistant" | "tool" | "system";

export interface ChatMessage {
  role: Role;
  content: string;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
}