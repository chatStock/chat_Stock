export async function streamChat(
  sessionId: string,
  message: string,
  onToken: (token: string) => void
) {
  const res = await fetch("http://localhost:8000/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
      message,
      session_id: sessionId
    }),
  });

  if (!res.body) throw new Error("No response body");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    onToken(decoder.decode(value));
  }
}