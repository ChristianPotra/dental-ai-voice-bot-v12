from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
import requests
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
        audio_url = f"{recording_url}.mp3"
        print("Downloading audio from:", audio_url)

        headers = {"User-Agent": "Mozilla/5.0"}
        audio = requests.get(audio_url, headers=headers)
        with open("temp.mp3", "wb") as f:
            f.write(audio.content)

        with open("temp.mp3", "rb") as f:
            whisper_response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        user_text = whisper_response.text
        print("Transcription:", user_text)

        gpt_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a friendly receptionist for a dental clinic in Melbourne."},
                {"role": "user", "content": user_text}
            ]
        )
        reply = gpt_response.choices[0].message.content
        print("GPT Response:", reply)

        response = VoiceResponse()
        response.say(reply)
        return str(response)

    except Exception as e:
        print(f"Error in /transcribe: {e}")
        response = VoiceResponse()
        response.say("Sorry, there was a problem processing your request. Please try again later.")
        return str(response)
    
    finally:
        try:
            os.remove("temp.mp3")
        except:
            pass

@app.route("/")
def home():
    return "Dental bot running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
