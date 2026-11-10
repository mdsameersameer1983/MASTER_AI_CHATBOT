# MASTER_AI_CHATBOT

A single, responsive AI chat dashboard with 10 specialist modes plus General AI, powered by Google's Gemini API. Upload a text-based PDF and ask questions about its contents in the same chat.

## Run locally

Requires Python 3.10 or newer.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Set `GEMINI_API_KEY` in your shell (never put a real key in source control). Optionally set `GEMINI_MODEL` to a model available to your API key. Then run:

```bash
python app.py
```

Open http://localhost:5000.

## Deploy on Render

1. Create a new Render Web Service from this project/repository, or use the included `render.yaml` as a Blueprint.
2. Use the Python runtime, build command `pip install -r requirements.txt`, and start command `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120`.
3. In **Environment**, add `GEMINI_API_KEY` with your secret Google AI Studio API key. It is deliberately not stored in this project. `GEMINI_MODEL` is optional and defaults to `gemini-2.5-flash`.
4. Deploy. Render provides `PORT`; Gunicorn serves the Flask WSGI application.

## Modes

General AI, Study Buddy, Code Master, Travel Mate, Career Guide, Chef Bot, English Master, Shopping Assistant, Fitness Buddy, Business Master, and PDF Genius.

PDF uploads are limited to 12 MB and the first 80 pages. Text extraction does not OCR scanned/image-only PDFs. Document text is held in browser memory for the current page session and sent to Gemini with your chat when you ask a question. Avoid uploading sensitive documents.
