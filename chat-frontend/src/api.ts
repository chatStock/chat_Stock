const API_BASE =
  import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function streamChat(
  sessionId: string,
  message: string,
  onToken: (token: string) => void
) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      session_id: sessionId,
    }),
  });

  if (!res.body) {
    throw new Error("No response body from backend");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    onToken(decoder.decode(value));
  }
}
