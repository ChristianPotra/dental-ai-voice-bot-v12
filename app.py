from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
import requests
import openai
import os

app = Flask(__name__)

# Load OpenAI API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/voice", methods=["POST"])
def voice():
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
    recording_url = request.form["RecordingUrl"] + ".mp3"
    audio = requests.get(recording_url)

    # Save audio to a temporary file
    with open("temp.mp3", "wb") as f:
        f.write(audio.content)

    # Transcribe with OpenAI Whisper
    with open("temp.mp3", "rb") as f:
        whisper_response = openai.Audio.transcribe(
            model="whisper-1",
            file=f
        )
    user_text = whisper_response["text"]

    # ChatGPT response
    gpt_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a friendly receptionist for a dental clinic in Melbourne."},
            {"role": "user", "content": user_text}
        ]
    )
    reply = gpt_response.choices[0].message.content

    # Reply back to caller
    response = VoiceResponse()
    response.say(reply)
    return str(response)

@app.route("/")
def home():
    return "Dental bot running"
