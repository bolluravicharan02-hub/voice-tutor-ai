from fastapi import FastAPI
from pydantic import BaseModel
import requests
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

chat_history = []

class Query(BaseModel):
    question: str
    mode: str
    voice: str


def get_voice_id(voice):
    if voice == "Teacher":
        return "en-US-natalie"
    elif voice == "Friendly":
        return "en-US-marcus"
    elif voice == "Kids":
        return "en-US-terrell"
    return "en-US-natalie"


def apply_mode(text, mode):
    if mode == "Simple":
        return "Explain in very simple words: " + text
    elif mode == "Exam":
        return "Explain like an exam answer: " + text
    elif mode == "Short":
        return "Explain in 3 lines: " + text
    return text


@app.get("/")
def home():
    return {"message": "VoiceTutor API running 🚀"}


@app.post("/ask")
def ask_ai(data: Query):
    try:
        question = apply_mode(data.question, data.mode)

        chat_history.append({"role": "user", "content": question})

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=chat_history
        )

        answer = response.choices[0].message.content

        chat_history.append({"role": "assistant", "content": answer})

        # Murf API
        url = "https://api.murf.ai/v1/speech/generate"

        payload = {
            "text": answer,
            "voiceId": get_voice_id(data.voice),
            "format": "mp3"
        }

        headers = {
            "api-key": os.getenv("MURF_API_KEY"),
            "Content-Type": "application/json"
        }
 
        res = requests.post(url, json=payload, headers=headers)

        murf_data = res.json()
        audio_url = murf_data.get("audioFile", "")

        return {
            "answer": answer,
            "audio": audio_url
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            "answer": str(e),   # 👈 VERY IMPORTANT
            "audio": ""
        }