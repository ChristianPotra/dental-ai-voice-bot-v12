from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
import requests
import os
import openai

# Initialize Flask app
app = Flask(__name__)

# Set OpenAI API key
openai.api_key = os.environ["OPENAI_API_KEY"]

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
        # Get the recording URL from Twilio (MP3)
        recording_url = request.form["RecordingUrl"]
        audio_url = f"{recording_url}.mp3"
        print(f"Downloading audio from: {audio_url}")

        # Download the audio file
        audio_response = requests.get(audio_url)
        with open("temp.mp3", "wb") as f:
            f.write(audio_response.content)

        # Transcribe with OpenAI Whisper
        with open("temp.mp3", "rb") as audio_file:
            whisper_response = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file
            )
        user_text = whisper_response["text"]
        print(f"User said: {user_text}")

        # Get GPT-4 response
        gpt_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a friendly receptionist for a dental clinic in Melbourne."},
                {"role": "user", "content": user_text}
            ]
        )
        reply = gpt_response.choices[0].message.content
        print(f"AI reply: {reply}")

        # Respond to the caller
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
    return "Dental bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
