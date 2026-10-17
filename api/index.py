import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from mangum import Mangum

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

class Message(BaseModel):
    message: str
    history: list = []

@app.post("/api/chat")
def chat(data: Message):
    if not client:
        raise HTTPException(status_code=500, detail="API Key not found")
    try:
        contents = []
        for h in data.history:
            role = "model" if h.get("role") == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": h.get("content", "")}]})
        contents.append({"role": "user", "parts": [{"text": data.message}]})

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=contents
        )
        return {"response": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

handler = Mangum(app)
