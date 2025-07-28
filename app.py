from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
import requests
import openai
import os

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/voice", methods=["POST"])
def voice():
    # Step 1: Greet and record
    response = VoiceResponse()
    response.say("Hi! This is your AI dental assistant. Please ask your question after the beep.")
    response.record(
        action="/transcribe",
        method="POST",
        max_length=10,
        play_beep=True
    )
    return str(response)

@app.route("/transcribe", methods=["POST"])
def transcribe():
    # Step 2: Get audio recording URL from Twilio
    recording_url = request.form["RecordingUrl"] + ".mp3"

    # Step 3: Download audio
    audio = requests.get(recording_url)

    # Step 4: Transcribe with OpenAI Whisper
    whisper_response = openai.Audio.transcribe(
        model="whisper-1",
        file=("voice.mp3", audio.content)
    )
    user_text = whisper_response["text"]

    # Step 5: Send to ChatGPT
    gpt_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a friendly receptionist for a dental clinic in Melbourne. Answer clearly and helpfully."},
            {"role": "user", "content": user_text}
        ]
    )
    reply = gpt_response["choices"][0]["message"]["content"]

    # Step 6: Say reply back to caller
    response = VoiceResponse()
    response.say(reply)
    return str(response)

@app.route("/")
def home():
    return "Dental bot running"

