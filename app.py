import os
from io import BytesIO

from flask import Flask, jsonify, render_template, request
from pypdf import PdfReader
from google import genai
from google.genai import types

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024

MODES = {
    "General AI": "Be a clear, thoughtful, helpful general-purpose assistant.",
    "Study Buddy": "Teach patiently. Explain concepts step by step, use examples, and encourage learning rather than just giving answers.",
    "Code Master": "Act as an experienced programming mentor. Give accurate code, explain decisions, and help debug systematically.",
    "Travel Mate": "Help plan practical trips. Ask about dates, budget, interests, and constraints when useful. Clearly flag details that may change.",
    "Career Guide": "Offer practical career, resume, interview, and skills guidance tailored to the user's goals.",
    "Chef Bot": "Suggest approachable recipes, substitutions, and clear cooking steps. Ask about dietary needs when relevant.",
    "English Master": "Help the user improve English kindly. Explain corrections and offer natural alternatives while adapting to their level.",
    "Shopping Assistant": "Help compare products against the user's needs, budget, and priorities. Be transparent about uncertainty and avoid inventing live prices.",
    "Fitness Buddy": "Offer sustainable general fitness and habit guidance. Adapt plans to the user's experience and equipment.",
    "Business Master": "Help with practical business planning, marketing, operations, and decision-making. State assumptions clearly.",
    "PDF Genius": "Answer questions grounded in the supplied PDF text. Cite page numbers when available and say when the document does not contain the answer.",
}


@app.get("/")
def home():
    return render_template("index.html", modes=list(MODES))


@app.post("/api/chat")
def chat():
    if not os.getenv("GEMINI_API_KEY"):
        return jsonify(error="GEMINI_API_KEY is not configured. Add it in your Render environment variables."), 503
    payload = request.get_json(silent=True) or {}
    mode = payload.get("mode", "General AI")
    message = (payload.get("message") or "").strip()
    history = payload.get("history") or []
    if mode not in MODES:
        return jsonify(error="Please choose a valid assistant mode."), 400
    if not message:
        return jsonify(error="Write a message before sending."), 400
    if len(message) > 12000:
        return jsonify(error="Your message is too long. Please keep it under 12,000 characters."), 413
    contents = []
    for item in history[-12:]:
        role = "model" if item.get("role") == "assistant" else "user"
        text = str(item.get("text", ""))[:4000]
        if text:
            contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))
    try:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        result = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=MODES[mode], temperature=0.7),
        )
        answer = result.text
        if not answer:
            return jsonify(error="The assistant returned an empty response. Please try again."), 502
        return jsonify(reply=answer)
    except Exception:
        app.logger.exception("Gemini request failed")
        return jsonify(error="The AI request could not be completed. Check your API key and try again."), 502


@app.post("/api/pdf")
def pdf_text():
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        return jsonify(error="Choose a PDF file first."), 400
    if not uploaded.filename.lower().endswith(".pdf"):
        return jsonify(error="Please choose a PDF file."), 400
    try:
        reader = PdfReader(BytesIO(uploaded.read()))
        pages = []
        for number, page in enumerate(reader.pages[:80], start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(f"[Page {number}]\n{text}")
        document = "\n\n".join(pages)
        if not document.strip():
            return jsonify(error="No selectable text was found. Scanned image PDFs need OCR before upload."), 422
        return jsonify(filename=uploaded.filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1], pages=min(len(reader.pages), 80), text=document[:90000])
    except Exception:
        return jsonify(error="This PDF could not be read. Try another file."), 400


@app.errorhandler(413)
def too_large(_error):
    return jsonify(error="That file is too large. The upload limit is 12 MB."), 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
