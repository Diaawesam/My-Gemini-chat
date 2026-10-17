import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from google import genai
from mangum import Mangum
import base64

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    message: str
    history: list = []
    image: Optional[str] = None

@app.post("/api/chat")
@app.post("/chat")
def chat(data: ChatMessage):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not provided in Vercel settings")
    
    try:
        client = genai.Client(api_key=api_key)

        contents = []
        for h in data.history:
            role = "model" if h.get("role") == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": h.get("content", "")}]})
        
        user_parts = [{"text": data.message if data.message else "صف هذه الصورة"}]
        
        if data.image:
            if "," in data.image:
                header, encoded = data.image.split(",", 1)
                mime_type = header.split(";")[0].replace("data:", "")
            else:
                encoded = data.image
                mime_type = "image/jpeg"
            
            user_parts.append({
                "inline_data": {
                    "mime_type": mime_type,
                    "data": encoded
                }
            })

        contents.append({"role": "user", "parts": user_parts})

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=contents
        )
        return {"response": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

handler = Mangum(app)
