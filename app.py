from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
import requests
from io import BytesIO
import os
from openai import OpenAI

app = Flask(__name__)
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
        recording_url = request.form["RecordingUrl"]
        audio = requests.get(recording_url)
        with open("temp.wav", "wb") as f:
            f.write(audio.content)

        with open("temp.wav", "rb") as f:
            whisper_response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )

        user_text = whisper_response.text

        gpt_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a friendly receptionist for a dental clinic in Melbourne."},
                {"role": "user", "content": user_text}
            ]
        )
        reply = gpt_response.choices[0].message.content

        response = VoiceResponse()
        response.say(reply)
        return str(response)

    except Exception as e:
        print(f"Error in /transcribe: {e}")
        response = VoiceResponse()
        response.say("Sorry, there was a problem processing your request. Please try again later.")
        return str(response)

@app.route("/")
def home():
    return "Dental bot running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
