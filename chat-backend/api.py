from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from agent_stream import stream_agent_reply

app = FastAPI()

# DEV ONLY CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    message = body.get("message")
    session_id = body.get("session_id", "default")  # Get session_id from request

    if not message:
        return {"error": "Missing message"}

    async def event_stream():
        async for chunk in stream_agent_reply(session_id, message):
            yield chunk

    return StreamingResponse(
        event_stream(),
        media_type="text/plain"
    )
