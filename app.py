from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI
import requests
import time
import os

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -----------------------
# GLOBAL STATE
# -----------------------
cache = {}
last_request_time = 0
request_count = {}  # <-- RATE LIMIT STORAGE (GLOBAL)


# -----------------------
# OPENALEX
# -----------------------
def search_openalex(query):
    try:
        r = requests.get(
            "https://api.openalex.org/works",
            params={
                "search": query,
                "per-page": 5
            },
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

    sources = []

    if any(x in q for x in ["lucy", "afarensis", "australopithecus", "hominin"]):
        sources = [
            ("Smithsonian Human Origins - Lucy", "https://humanorigins.si.edu/evidence/human-fossils/species/australopithecus-afarensis"),
            ("Britannica - Australopithecus afarensis", "https://www.britannica.com/topic/Australopithecus-afarensis")
        ]

    elif any(x in q for x in ["dead sea scrolls", "qumran", "scrolls"]):
        sources = [
            ("Britannica - Dead Sea Scrolls", "https://www.britannica.com/topic/Dead-Sea-Scrolls"),
            ("Israel Museum - Dead Sea Scrolls", "https://www.imj.org.il/en/wings/archaeology/dead-sea-scrolls")
        ]

    elif any(x in q for x in ["pompeii", "vesuvius"]):
        sources = [
            ("Pompeii Archaeological Park", "https://pompeiisites.org/"),
            ("UNESCO World Heritage - Pompeii", "https://whc.unesco.org/en/list/829/")
        ]

    return sources


# -----------------------
# FORMAT REFERENCES
# -----------------------
def format_refs(nodes, fallback):
    formatted = []

    if nodes:
        for n in nodes:
            if n.get("url"):
                formatted.append(f"• {n['title']} ({n['year']})\n  {n['url']}")
            else:
                formatted.append(f"• {n['title']} ({n['year']})")
    else:
        for name, url in fallback:
            formatted.append(f"• {name}\n  {url}")

    return "\n".join(formatted)


# -----------------------
# HOME
# -----------------------
@app.route("/")
def home():
    return send_from_directory(".", "index.html")


# -----------------------
# CHAT ENDPOINT
# -----------------------
@app.route("/chat", methods=["POST"])
def chat():

    global last_request_time

    try:
        data = request.json or {}
        message = (data.get("message") or "").strip()

        if not message:
            return jsonify({"reply": "Empty message", "references": ""})

        # -----------------------
        # SIMPLE RATE LIMIT (global)
        # -----------------------
        ip = request.remote_addr
        now = time.time()

        window = 3600  # 1 hour
        limit = 50     # max requests per hour per IP

        if ip not in request_count:
            request_count[ip] = []

        # remove old timestamps
        request_count[ip] = [t for t in request_count[ip] if now - t < window]

        if len(request_count[ip]) >= limit:
            return jsonify({
                "reply": "Rate limit reached. Please try later.",
                "references": ""
            }), 429

        request_count[ip].append(now)

        # -----------------------
        # GLOBAL RATE LIMIT (anti spam)
        # -----------------------
        if now - last_request_time < 1:
            return jsonify({
                "reply": "Too many requests. Please wait.",
                "references": ""
            }), 429

        last_request_time = now

        # -----------------------
        # CACHE
        # -----------------------
        if message in cache:
            return jsonify(cache[message])

        # -----------------------
        # SOURCES
        # -----------------------
        nodes = search_openalex(message)
        fallback = fallback_sources(message)
        refs_text = format_refs(nodes, fallback)

        # -----------------------
        # SYSTEM PROMPT
        # -----------------------
        system_prompt = """
You are ATHENA, an expert assistant in archaeology, paleoanthropology, and ancient history.

RULES:
- Be clear and factual
- Avoid unnecessary verbosity
- Always ground answers in archaeological context
- If uncertain, say so briefly
"""

        # -----------------------
        # OPENAI CALL
        # -----------------------
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"""
QUESTION:
{message}

REFERENCES:
{refs_text}
"""
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
        return jsonify({
            "reply": f"Server error: {str(e)}",
            "references": ""
        }), 500


# -----------------------
# RUN APP
# -----------------------
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
