import os
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
import requests
import openai

# --- Config ---
openai.api_key = os.environ.get("OPENAI_API_KEY")  # DO NOT put your key in code
TWILIO_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.environ.get("TWILIO_AUTH_TOKEN")

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Dental AI Voice Bot (legacy OpenAI SDK) is running", 200

@app.route("/voice", methods=["POST"])
def voice():
    vr = VoiceResponse()
    vr.say("Hi! This is your AI dental assistant. Please ask your question after the beep.", voice="alice", language="en-AU")
    vr.record(
        action="/transcribe",
        method="POST",
        max_length=20,
        trim="trim-silence",
        play_beep=True
    )
    # In case caller doesn't say anything
    vr.say("Goodbye!", voice="alice", language="en-AU")
    return str(vr)

@app.route("/transcribe", methods=["POST"])
def transcribe():
    vr = VoiceResponse()
    try:
        recording_url = request.form.get("RecordingUrl")
        if not recording_url:
            vr.say("Sorry, I couldn't access your recording.", voice="alice", language="en-AU")
            return str(vr)

        # Twilio gives URL without extension; append .mp3
        audio_url = f"{recording_url}.mp3"
        print("Downloading audio from:", audio_url)

        # Some Twilio accounts require auth to fetch recordings
        auth_tuple = (TWILIO_SID, TWILIO_AUTH) if (TWILIO_SID and TWILIO_AUTH) else None
        r = requests.get(audio_url, auth=auth_tuple, timeout=20)
        r.raise_for_status()

        # Sanity check we actually got audio, not HTML
        ctype = r.headers.get("Content-Type", "")
        if "audio" not in ctype and "octet-stream" not in ctype:
            print("Non-audio response from Twilio recording URL. Content-Type:", ctype)
            print("First 200 bytes:", r.content[:200])
            vr.say("Sorry, I couldn't read your message. Please try again.", voice="alice", language="en-AU")
            return str(vr)

        # Save to a temp file for Whisper
        temp_path = "temp.mp3"
        with open(temp_path, "wb") as f:
            f.write(r.content)

        # --- OpenAI legacy SDK (0.28.1) transcribe ---
        with open(temp_path, "rb") as f:
            tr = openai.Audio.transcribe("whisper-1", f)
        user_text = tr.get("text", "").strip()
        print("Transcribed:", user_text)

        if not user_text:
            vr.say("I didn't catch that. Could you repeat your question?", voice="alice", language="en-AU")
            return str(vr)

        # --- Chat reply ---
        completion = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # any current chat model name works with 0.28 client
            messages=[
                {"role": "system", "content": "You are a friendly, reliable receptionist for a Melbourne dental clinic. Keep replies concise and helpful."},
                {"role": "user", "content": user_text}
            ],
            temperature=0.4
        )
        reply = completion.choices[0].message["content"].strip()
        print("Reply:", reply)

        vr.say(reply, voice="alice", language="en-AU")
        return str(vr)

    except Exception as e:
        print("Error in /transcribe:", e)
        vr.say("Sorry, there was a problem processing your request. Please try again later.", voice="alice", language="en-AU")
        return str(vr)

if __name__ == "__main__":
    # Local dev: Render uses gunicorn via Start Command instead
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
