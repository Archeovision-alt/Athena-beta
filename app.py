from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI
import requests
import time
import os

app = Flask(__name__)
CORS(app)

# -----------------------
# OPENAI CLIENT
# -----------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -----------------------
# MEMORY
# -----------------------
cache = {}
request_count = {}
last_request_time = 0

# -----------------------
# ARCHEO NEWS (SEED SIMPLE)
# -----------------------
ARCHAEO_NEWS = [
    {
        "title": "Göbekli Tepe continues to reshape early human history",
        "year": 2024,
        "url": "https://www.archaeology.org"
    },
    {
        "title": "New findings at Pompeii excavation sites",
        "year": 2023,
        "url": "https://www.britannica.com/place/Pompeii"
    },
    {
        "title": "DNA analysis reshapes Neanderthal migration models",
        "year": 2024,
        "url": "https://www.nature.com"
    }
]

# -----------------------
# HOME
# -----------------------
@app.route("/")
def home():
    return send_from_directory(".", "index.html")

# -----------------------
# NEWS ENDPOINT
# -----------------------
@app.route("/news", methods=["GET"])
def news():
    return jsonify(ARCHAEO_NEWS)

# -----------------------
# CHAT
# -----------------------
@app.route("/chat", methods=["POST"])
def chat():
    global last_request_time

    try:
        data = request.json or {}
        message = (data.get("message") or "").strip()

        if not message:
            return jsonify({"reply": "Empty message", "references": ""})

        # simple anti spam
        now = time.time()
        if now - last_request_time < 1:
            return jsonify({"reply": "Too many requests", "references": ""}), 429
        last_request_time = now

        # cache
        if message in cache:
            return jsonify(cache[message])

        system_prompt = """
You are ATHENA, Archaeological Research Assistant.

Rules:
- concise answers
- factual archaeology focus
- if uncertain say so briefly
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=800
        )

        reply = response.choices[0].message.content

        result = {
            "reply": reply,
            "references": ""
        }

        cache[message] = result
        return jsonify(result)

    except Exception as e:
        return jsonify({"reply": str(e), "references": ""}), 500


# -----------------------
# RUN
# -----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
