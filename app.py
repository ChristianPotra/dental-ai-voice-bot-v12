from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
import requests
import os
from openai import OpenAI

app = Flask(__name__)

# Initialize OpenAI client with your API key from environment variables
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
        print(f"Downloading audio from: {audio_url}")

        # Download the recorded audio from Twilio
        audio_response = requests.get(audio_url)
        audio_response.raise_for_status()  # Raise error if download fails

        # Save to a temp file
        with open("temp.mp3", "wb") as f:
            f.write(audio_response.content)

        # Open the file and send it to OpenAI Whisper for transcription
        with open("temp.mp3", "rb") as audio_file:
            whisper_response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

        user_text = whisper_response.text
        print(f"Transcribed text: {user_text}")

        # Generate a response from GPT-4 based on the transcription
        chat_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a friendly receptionist for a dental clinic in Melbourne."},
                {"role": "user", "content": user_text}
            ]
        )

        reply = chat_response.choices[0].message.content
        print(f"GPT reply: {reply}")

        # Respond to caller with the generated reply
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
    # Run on the port assigned by your environment (e.g., Render)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
