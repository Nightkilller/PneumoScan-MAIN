import os
import uuid
import json
import numpy as np
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file
from PIL import Image
import tensorflow as tf
from utils.pdf_report import generate_report

# ── Flask app ───────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB limit

UPLOAD_FOLDER = os.path.join(app.static_folder, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── Load model once at startup ──────────────────────────────────────────
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "pneumonia_model.keras")
print(f"[PneumoScan] Loading model from {MODEL_PATH} …")
model = tf.keras.models.load_model(MODEL_PATH)
print("[PneumoScan] Model loaded successfully ✓")

# ── Helpers ──────────────────────────────────────────────────────────────
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "webp"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def preprocess_image(image_path: str) -> np.ndarray:
    """Resize → RGB → normalize → expand dims."""
    img = Image.open(image_path).convert("RGB").resize((224, 224))
    arr = np.array(img) / 255.0
    return np.expand_dims(arr, axis=0)


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

    # --- run prediction ---
    try:
        processed = preprocess_image(filepath)
        prediction = model.predict(processed, verbose=0)

        # Support both single-output (sigmoid) and two-output (softmax) models
        if prediction.shape[-1] == 1:
            pneumonia_prob = float(prediction[0][0])
            normal_prob = 1.0 - pneumonia_prob
        else:
            normal_prob = float(prediction[0][0])
            pneumonia_prob = float(prediction[0][1])

        label = "PNEUMONIA" if pneumonia_prob >= 0.5 else "NORMAL"
        confidence = round(max(pneumonia_prob, normal_prob) * 100, 2)

        return jsonify({
            "prediction": label,
            "confidence": confidence,
            "pneumonia_prob": round(pneumonia_prob * 100, 2),
            "normal_prob": round(normal_prob * 100, 2),
            "image_filename": filename,
            "patient_name": patient_name,
            "patient_age": patient_age,
            "notes": notes,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
    app.run(debug=True)
