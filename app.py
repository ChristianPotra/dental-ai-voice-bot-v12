from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse
from openai import OpenAI
import os

app = Flask(__name__)

# Create OpenAI client (no proxies arg)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/voice", methods=["POST"])
def voice():
    """Handle incoming call from Twilio and prompt for speech."""
    response = VoiceResponse()
    response.say("Hello, please speak after the beep. I will process your request.")
    response.record(
        action="/transcribe",
        max_length=30,
        transcribe=False,
        play_beep=True
    )
    return Response(str(response), mimetype='application/xml')

@app.route("/transcribe", methods=["POST"])
def transcribe():
    """Handle the recorded audio, transcribe it, and respond with AI."""
    recording_url = request.form.get("RecordingUrl")
    if not recording_url:
        vr = VoiceResponse()
        vr.say("Sorry, I could not get your recording.")
        return Response(str(vr), mimetype='application/xml')

    # Download the audio file from Twilio
    import requests
    audio_file = requests.get(f"{recording_url}.wav")

    # Save temporarily
    with open("temp.wav", "wb") as f:
        f.write(audio_file.content)

    # Transcribe using OpenAI Whisper
    with open("temp.wav", "rb") as audio:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio
        )

    user_text = transcript.text

    # Generate AI response using GPT
    ai_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful dental clinic receptionist."},
            {"role": "user", "content": user_text}
        ]
    )

    answer = ai_response.choices[0].message.content

    # Reply via Twilio
    vr = VoiceResponse()
    vr.say(answer)
    return Response(str(vr), mimetype='application/xml')

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)