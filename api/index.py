import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
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

class ChatMessage(BaseModel):
    message: str
    history: list = []
    image: Optional[str] = None

@app.post("/api/chat")
@app.post("/chat")
def chat(data: ChatMessage):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY غير موجود في إعدادات Vercel")
    
    try:
        client = genai.Client(api_key=api_key)

        # تجهيز المحادثة السابقة بشكل محمي
        contents = []
        for h in data.history:
            role = "model" if h.get("role") == "assistant" else "user"
            contents.append({
                "role": role,
                "parts": [{"text": h.get("content", "")}]
            })
        
        # إضافة الرسالة الحالية
        user_parts = []
        if data.message:
            user_parts.append({"text": data.message})
            
        if data.image:
            # التعامل مع الصورة كـ inline_data
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

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=contents
        )
        return {"response": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"حدث خطأ أثناء المعالجة: {str(e)}")

handler = Mangum(app)
