import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from google import genai
from google.genai import types
from mangum import Mangum

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
    history: Optional[List[dict]] = []
    image: Optional[str] = None
    system_prompt: Optional[str] = None

@app.post("/api/chat")
@app.post("/chat")
def chat(data: ChatMessage):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY غير موجود في إعدادات Vercel")
    
    try:
        client = genai.Client(api_key=api_key)

        contents = []
        if data.history:
            for h in data.history:
                role = "model" if h.get("role") == "assistant" else "user"
                content_text = h.get("content", "")
                if content_text:
                    contents.append({
                        "role": role,
                        "parts": [{"text": str(content_text)}]
                    })
        
        user_parts = []
        if data.message:
            user_parts.append({"text": str(data.message)})
            
        if data.image:
            img_data = data.image
            mime_type = "image/jpeg"
            if "," in img_data:
                header, img_data = img_data.split(",", 1)
                mime_type = header.split(";")[0].replace("data:", "")
            
            user_parts.append({
                "inline_data": {
                    "mime_type": mime_type,
                    "data": img_data
                }
            })

        if not user_parts:
            user_parts.append({"text": "مرحباً"})

        contents.append({"role": "user", "parts": user_parts})

        config = None
        if data.system_prompt:
            config = types.GenerateContentConfig(system_instruction=data.system_prompt)

        # تفعيل التدفق المباشر للردود
        response = client.models.generate_content_stream(
            model="gemini-3.8-flash",
            contents=contents,
            config=config
        )

        def generate():
            try:
                for chunk in response:
                    if hasattr(chunk, 'text') and chunk.text:
                        yield chunk.text
            except Exception as e:
                yield f"\n[خطأ أثناء التوليد: {str(e)}]"

        return StreamingResponse(generate(), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

handler = Mangum(app)
