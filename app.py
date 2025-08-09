from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
import requests
import os
from openai import OpenAI

app = Flask(__name__)

# Create OpenAI client (no proxies argument)
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

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
    try:
        # Download Twilio recording
        recording_url = request.form["RecordingUrl"]
        audio_url = f"{recording_url}.mp3"
        print("Downloading audio from:", audio_url)

        audio_data = requests.get(audio_url)
        with open("temp.mp3", "wb") as f:
            f.write(audio_data.content)

        # Transcribe with Whisper
        with open("temp.mp3", "rb") as f:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        user_text = transcription.text
        print(f"User said: {user_text}")

        # Get GPT response
        chat_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a friendly receptionist for a dental clinic in Melbourne."},
                {"role": "user", "content": user_text}
            ]
        )
        reply = chat_response.choices[0].message.content
        print(f"Bot reply: {reply}")

        # Reply with audio to caller
        response = VoiceResponse()
        response.say(reply)
        return str(response)

    except Exception as e:
        print(f"Error in /transcribe: {e}")
        response = VoiceResponse()
        response.say("Sorry, there was a problem processing your request.")
        return str(response)

@app.route("/")
def home():
    return "Dental bot running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

