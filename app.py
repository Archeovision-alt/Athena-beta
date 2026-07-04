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
# GLOBAL STATE
# -----------------------
cache = {}
last_request_time = 0
request_count = {}

# -----------------------
# OPENALEX SEARCH
# -----------------------
def search_openalex(query):
    try:
        r = requests.get(
            "https://api.openalex.org/works",
            params={"search": query, "per-page": 5},
            timeout=8
        )

        data = r.json()
        nodes = []

        for item in (data.get("results") or [])[:5]:
            title = item.get("title")
            if not title:
                continue

            url = (
                (item.get("primary_location") or {}).get("landing_page_url")
                or item.get("doi")
                or item.get("id")
                or ""
            )

            nodes.append({
                "title": title,
                "year": item.get("publication_year") or "unknown",
                "url": url
            })

        return nodes

    except Exception as e:
        print("OpenAlex error:", e)
        return []

# -----------------------
# FALLBACK SOURCES
# -----------------------
def fallback_sources(query):
    q = query.lower()

    if any(x in q for x in ["lucy", "afarensis", "australopithecus"]):
        return [
            ("Smithsonian - Lucy", "https://humanorigins.si.edu"),
            ("Britannica - Australopithecus", "https://www.britannica.com")
        ]

    return []

# -----------------------
# FORMAT REFS
# -----------------------
def format_refs(nodes, fallback):
    if nodes:
        return "\n".join(
            f"• {n['title']} ({n['year']})\n  {n['url']}" for n in nodes
        )
    return "\n".join(f"• {name}\n  {url}" for name, url in fallback)

# -----------------------
# HOME
# -----------------------
@app.route("/")
def home():
    return send_from_directory(".", "index.html")

# -----------------------
# DEBUG ROUTE
# -----------------------
@app.route("/debug")
def debug():
    return "ATHENA VERSION 1.0.7 TEST OK"

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

        # simple rate limit
        now = time.time()
        ip = request.remote_addr

        request_count.setdefault(ip, [])
        request_count[ip] = [t for t in request_count[ip] if now - t < 3600]

        if len(request_count[ip]) >= 50:
            return jsonify({"reply": "Rate limit reached", "references": ""}), 429

        request_count[ip].append(now)

        if now - last_request_time < 1:
            return jsonify({"reply": "Too fast", "references": ""}), 429

        last_request_time = now

        # cache
        if message in cache:
            return jsonify(cache[message])

        # sources
        nodes = search_openalex(message)
        fallback = fallback_sources(message)
        refs_text = format_refs(nodes, fallback)

        # system prompt
        system_prompt = """
You are ATHENA, an archaeological research assistant.
Be concise, factual, grounded in evidence.
"""

        # OpenAI call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"QUESTION:\n{message}\n\nREFERENCES:\n{refs_text}"
                }
            ],
            max_tokens=900
        )

        reply = response.choices[0].message.content

        result = {
            "reply": reply,
            "references": refs_text
        }

        cache[message] = result
        return jsonify(result)

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"reply": str(e), "references": ""}), 500


# -----------------------
# RUN (IMPORTANT RENDER SAFE)
# -----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
