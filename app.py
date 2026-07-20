from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def load_athena_prompt():
    try:
        with open(
            "athena/prompt.txt",
            "r",
            encoding="utf-8"
        ) as file:
            return file.read()

    except Exception:
        return (
            "You are ATHENA, an artificial intelligence specialized "
            "in archaeology, history and human evolution."
        )


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():

    data = request.json
    question = data.get("question", "").strip()

    if not question:
        return jsonify({
            "answer": "Please enter a question."
        })

    prompt = load_athena_prompt()

    try:

        response = client.chat.completions.create(

            model="gpt-4.1-mini",

            messages=[
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": question
                }
            ],

            temperature=0.4

        )

        answer = response.choices[0].message.content

        return jsonify({
            "answer": answer
        })

    except Exception as e:

        print(e)

        return jsonify({
            "answer": f"ATHENA Error:\n\n{e}"
        })


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )