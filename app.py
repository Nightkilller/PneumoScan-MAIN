import os
import uuid
import json
import numpy as np
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, send_file
from PIL import Image
import tensorflow as tf
from utils.pdf_report import generate_report

# ── Flask app ───────────────────────────────────────────────────────────
load_dotenv()
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB limit

# ── Groq Setup ──────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.1-8b-instant"
groq_client = None

if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        print("[PneumoScan] Groq AI assistant loaded ✓")
        print(f"[PneumoScan] Using model: {GROQ_MODEL}")
    except Exception as e:
        print(f"[PneumoScan] Failed to initialize Groq: {e}")
else:
    print("[PneumoScan] Warning: GROQ_API_KEY not found. AI assistant disabled.")

# ── Global Context for Chat ─────────────────────────────────────────────
latest_analysis = {}

UPLOAD_FOLDER = os.path.join(app.static_folder, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── Load BOTH models once at startup ────────────────────────────────────
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

print("[PneumoScan] Loading X-ray detector model …")
xray_model = tf.keras.models.load_model(os.path.join(MODELS_DIR, "xray_detector.keras"))
print("[PneumoScan] X-ray detector loaded ✓")

print("[PneumoScan] Loading pneumonia classifier model …")
pneumonia_model = tf.keras.models.load_model(os.path.join(MODELS_DIR, "pneumonia_model.keras"))
print("[PneumoScan] Pneumonia classifier loaded ✓")

# ── Helpers ──────────────────────────────────────────────────────────────
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "webp"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def preprocess_image(image_path: str) -> np.ndarray:
    """Resize → RGB → normalize → expand dims."""
    img = Image.open(image_path).convert("RGB").resize((224, 224))
    arr = np.array(img) / 255.0
    return np.expand_dims(arr, axis=0)


XRAY_THRESHOLD = 0.5  # Stage-1 gate: xray_detector output must be ≥ this


# ── Routes ───────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    # --- validate inputs ---
    patient_name = request.form.get("patient_name", "").strip()
    patient_age = request.form.get("patient_age", "").strip()
    notes = request.form.get("notes", "").strip()
    file = request.files.get("xray")

    if not file or not allowed_file(file.filename):
        return jsonify({"error": "Please upload a valid image (png, jpg, jpeg, bmp, webp)."}), 400

    # --- save uploaded file ---
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # --- Preprocess once, reuse for both models ---
    try:
        processed = preprocess_image(filepath)
    except Exception:
        return jsonify({
            "prediction": "Invalid Image",
            "message": "Could not process the uploaded file. Please upload a valid image.",
        })

    # ── STAGE 1: X-ray detector ──────────────────────────────────────
    try:
        xray_pred = float(xray_model.predict(processed, verbose=0)[0][0])
        print(f"[PneumoScan] X-ray detector score: {xray_pred:.4f}")

        if xray_pred < XRAY_THRESHOLD:
            return jsonify({
                "prediction": "Invalid Image",
                "message": "This does not appear to be a chest X-ray. Please upload a valid chest X-ray image.",
            })
    except Exception as e:
        return jsonify({"error": f"X-ray detection failed: {e}"}), 500

    # ── STAGE 2: Pneumonia classifier ────────────────────────────────
    try:
        pred = float(pneumonia_model.predict(processed, verbose=0)[0][0])

        if pred > 0.5:
            label = "PNEUMONIA"
            confidence = round(pred * 100, 2)
        else:
            label = "NORMAL"
            confidence = round((1 - pred) * 100, 2)

        pneumonia_pct = round(pred * 100, 2)
        normal_pct = round((1 - pred) * 100, 2)

        # ── Store context for AI Chat ──
        global latest_analysis
        latest_analysis = {
            "prediction": label,
            "confidence": confidence,
            "patient_name": patient_name or "the patient",
            "pneumonia_prob": pneumonia_pct,
            "normal_prob": normal_pct,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        return jsonify({
            "prediction": label,
            "confidence": confidence,
            "pneumonia_prob": pneumonia_pct,
            "normal_prob": normal_pct,
            "image_filename": filename,
            "patient_name": patient_name,
            "patient_age": patient_age,
            "notes": notes,
        })
    except Exception as e:
        return jsonify({"error": f"Pneumonia prediction failed: {e}"}), 500


@app.route("/chat", methods=["POST"])
def chat():
    if not groq_client:
        return jsonify({"reply": "AI assistant is temporarily unavailable. Please try again later."}), 200

    user_msg = request.json.get("message", "").strip()
    if not user_msg:
        return jsonify({"reply": "Please say something."}), 400

    # ── Context Construction ──
    context_str = ""
    if latest_analysis:
        context_str = (
            f"Current Analysis Report:\n"
            f"- Patient: {latest_analysis.get('patient_name')}\n"
            f"- Prediction: {latest_analysis.get('prediction')}\n"
            f"- Confidence: {latest_analysis.get('confidence')}%\n"
            f"- Pneumonia Probability: {latest_analysis.get('pneumonia_prob')}%\n"
            f"- Normal Probability: {latest_analysis.get('normal_prob')}%\n"
            f"- Analysis Time: {latest_analysis.get('timestamp')}\n"
        )
    else:
        context_str = "No analysis report is currently available.\n"

    # ── System Prompt ──
    system_prompt = (
        "You are PneumoBot, an expert AI medical assistant for lung health, "
        "built into the PneumoScan AI diagnostic platform.\n\n"
        f"{context_str}\n"
        "Your Rules:\n"
        "1. Answer questions about pneumonia, lung health, and the current report.\n"
        "2. Explain the AI prediction clearly to the user.\n"
        "3. If Prediction is PNEUMONIA, suggest consulting a pulmonologist immediately.\n"
        "4. Provide general advice on precautions (rest, fluids, isolation) if relevant.\n"
        "5. You may mention common medicine categories (e.g. antibiotics, antivirals) as "
        "general information if asked, but NEVER prescribe specific drugs or dosages.\n"
        "6. Always include a short disclaimer: \"I am an AI, not a doctor. Please consult a specialist.\"\n"
        "7. Keep answers concise (under 3-4 sentences) and empathetic.\n"
    )

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.7,
            max_tokens=512,
        )
        reply = response.choices[0].message.content
        return jsonify({"reply": reply})
    except Exception as e:
        print(f"[PneumoScan] Chat error: {e}")
        return jsonify({"reply": "AI assistant is temporarily unavailable. Please try again later."}), 500


@app.route("/download-report", methods=["POST"])
def download_report():
    data = request.get_json(force=True)

    patient_name = data.get("patient_name", "N/A")
    patient_age = data.get("patient_age", "N/A")
    notes = data.get("notes", "")
    prediction = data.get("prediction", "N/A")
    confidence = data.get("confidence", 0)
    pneumonia_prob = data.get("pneumonia_prob", 0)
    normal_prob = data.get("normal_prob", 0)
    image_filename = data.get("image_filename", "")

    image_path = os.path.join(UPLOAD_FOLDER, image_filename) if image_filename else None
    if image_path and not os.path.exists(image_path):
        image_path = None

    report_name = f"report_{uuid.uuid4().hex[:8]}.pdf"
    report_path = os.path.join(UPLOAD_FOLDER, report_name)

    generate_report(
        output_path=report_path,
        patient_name=patient_name,
        patient_age=patient_age,
        notes=notes,
        prediction=prediction,
        confidence=confidence,
        pneumonia_prob=pneumonia_prob,
        normal_prob=normal_prob,
        image_path=image_path,
    )

    return send_file(report_path, as_attachment=True, download_name="PneumoScan_Report.pdf")


# ── Main ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[PneumoScan] Server running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
