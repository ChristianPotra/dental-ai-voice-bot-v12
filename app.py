import os
from flask import Flask, request, jsonify
from openai import OpenAI
from twilio.twiml.voice_response import VoiceResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/", methods=["GET"])
def home():
    return "Dental AI Voice Bot is running!", 200

@app.route("/voice", methods=["POST"])
def voice():
    response = VoiceResponse()
    response.say("Hello! This is the dental AI assistant. How can I help you today?")
    return str(response)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful dental receptionist AI."},
            {"role": "user", "content": user_message}
        ]
    )
    ai_response = completion.choices[0].message.content
    return jsonify({"response": ai_response})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
