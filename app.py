import os
import time
import requests
from flask import Flask, request, jsonify
from twilio.twiml.voice_response import VoiceResponse
from openai import OpenAI
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/", methods=["GET"])
def home():
    return "Dental AI Voice Bot is running!", 200

@app.route("/voice", methods=["POST"])
def voice():
    response = VoiceResponse()
    response.say("Hello! This is your dental AI assistant. Please speak after the beep.")
    # Add recording status callback
    response.record(
        action="/transcribe",  # endpoint when recording finishes
        method="POST",
        max_length=30,
        play_beep=True,
        recording_status_callback="/transcribe",  # called when recording is ready
        recording_status_callback_method="POST"
    )
    return str(response)

@app.route("/transcribe", methods=["POST"])
def transcribe():
    recording_sid = request.form.get("RecordingSid")
    if not recording_sid:
        return jsonify({"error": "No recording SID provided"}), 400

    # Build the secure Twilio recording URL
    audio_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Recordings/{recording_sid}.mp3"

    # Retry a few times if recording isn’t ready yet
    for attempt in range(5):
        response = requests.get(audio_url, auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
        if response.status_code == 200:
            break
        time.sleep(1)  # wait 1 second and retry
    else:
        return jsonify({"error": f"Recording not found after retries: {audio_url}"}), 404

    # Save to temp file
    with open("temp.mp3", "wb") as f:
        f.write(response.content)

    # Transcribe with OpenAI
    with open("temp.mp3", "rb") as f:
        transcription = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=f
        )

    user_text = transcription.text

    # Generate AI response
    chat_completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful dental receptionist AI."},
            {"role": "user", "content": user_text}
        ]
    )
    reply = chat_completion.choices[0].message.content

    # Return voice response
    twilio_response = VoiceResponse()
    twilio_response.say(reply)
    return str(twilio_response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
