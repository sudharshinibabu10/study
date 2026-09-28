import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

import chatbot_config as cfg

load_dotenv()

app = Flask(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MAX_HISTORY = 20
MAX_MESSAGE_LENGTH = 2000


@app.route("/")
def home():
    return render_template(
        "index.html",
        name=cfg.BOT_NAME,
        tagline=cfg.TAGLINE,
        welcome=cfg.WELCOME,
        suggestions=cfg.SUGGESTIONS,
    )


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()[:MAX_MESSAGE_LENGTH]

    if not message:
        return jsonify(error="Please type a question."), 400

    contents = []
    for item in data.get("history", [])[-MAX_HISTORY:]:
        if item.get("role") in ("user", "model") and item.get("text"):
            contents.append(
                types.Content(role=item["role"], parts=[types.Part(text=item["text"])])
            )
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

    try:
        response = client.models.generate_content(
            model=cfg.MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=cfg.SYSTEM_PROMPT,
                temperature=0.5,
            ),
        )
        return jsonify(reply=response.text or cfg.EMPTY_REPLY)
    except Exception:
        return jsonify(error="Something went wrong. Please try again."), 500


if __name__ == "__main__":
    app.run(debug=True)
