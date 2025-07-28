from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse

app = Flask(__name__)

@app.route("/voice", methods=["POST"])
def voice():
    resp = VoiceResponse()
    resp.say("Hello! This is your AI dental assistant. How can I help you today?")
    return str(resp)

@app.route("/")
def index():
    return "App is running!"
