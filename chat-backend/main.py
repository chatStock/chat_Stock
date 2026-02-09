from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from agent_stream import stream_agent_reply
import uuid

app = FastAPI(title="Stock Chat Backend")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "stock-chat-backend"}


@app.post("/chat")
async def chat(request: ChatRequest):
    """Non-streaming chat endpoint"""
    session_id = request.session_id or str(uuid.uuid4())
    
    # Collect full response
    response_text = ""
    async for chunk in stream_agent_reply(session_id, request.message):
        response_text += chunk
    
    return {
        "response": response_text,
        "session_id": session_id
    }


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint"""
    session_id = request.session_id or str(uuid.uuid4())
    
    async def generate():
        async for chunk in stream_agent_reply(session_id, request.message):
            # SSE format
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)