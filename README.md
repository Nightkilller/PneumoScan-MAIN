# 🫁 PneumoScan — AI Pneumonia Detection

A production-ready, Dockerized AI web application that detects **pneumonia from chest X-ray images** using deep learning, with an integrated AI medical assistant and PDF diagnostic reports.

> *🔴 Live Demo:** [https://pneumoscan-main.onrender.com](https://pneumoscan-main.onrender.com) 

---

## ✨ Features

- **Two-Stage AI Analysis** — X-ray validation + pneumonia classification
- **Real-Time Prediction** — Upload a chest X-ray and get instant results
- **AI Medical Assistant** — Powered by Groq (LLaMA 3.1) for follow-up Q&A
- **PDF Diagnostic Reports** — Download professional hospital-style reports
- **Modern UI** — Responsive, dark-themed medical interface with 3D lung animation
- **Dockerized** — Reproducible builds, no dependency issues

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.10, Flask, Gunicorn |
| **AI/ML** | TensorFlow 2.15.0 / Keras (CNN) |
| **AI Chat** | Groq API (LLaMA 3.1 8B) |
| **Frontend** | HTML5, CSS3, Vanilla JS |
| **PDF Engine** | ReportLab + Matplotlib |
| **Container** | Docker (Python 3.10-slim) |
| **Deployment** | Render (Docker) |

---

## 📁 Project Structure

```
PneumoScan/
├── app.py                      # Flask backend + routes
├── Dockerfile                  # Production container
├── .dockerignore               # Docker build exclusions
├── requirements.txt            # Pinned dependencies
├── .gitignore                  # Git exclusions
├── README.md                   # This file
├── models/
│   ├── pneumonia_model.keras   # Pneumonia classifier (~11 MB)
│   └── xray_detector.keras     # X-ray validator (~10 MB)
├── static/
│   ├── css/style.css           # UI styles
│   └── js/
│       ├── main.js             # Core app logic
│       ├── charts.js           # Confidence chart rendering
│       └── lungs3d.js          # 3D lung animation
├── templates/
│   └── index.html              # Main page
└── utils/
    ├── __init__.py
    └── pdf_report.py           # PDF report generator
```

---

## 🐳 Run Locally with Docker

```bash
# 1. Clone the repository
git clone https://github.com/Nightkilller/PneumoScan-MAIN.git
cd PneumoScan-MAIN

# 2. Build the Docker image
docker build -t pneumoscan .

# 3. Run the container
docker run -p 10000:10000 -e GROQ_API_KEY=your_key_here pneumoscan
```



---

## 🚀 Run Locally without Docker

```bash
# 1. Clone and enter project
git clone https://github.com/Nightkilller/PneumoScan-MAIN.git
cd PneumoScan-MAIN

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
echo "GROQ_API_KEY=your_key_here" > .env

# 5. Run
python3 app.py
```

---

## 🧠 Model Details

| Model | Purpose | Architecture | Input |
|-------|---------|-------------|-------|
| `xray_detector.keras` | Validates if image is a chest X-ray | CNN (224×224 RGB) | Chest image |
| `pneumonia_model.keras` | Classifies Normal vs Pneumonia | CNN (224×224 RGB) | Chest X-ray |

- **Stage 1:** X-ray detector gates invalid uploads (score ≥ 0.5 required)
- **Stage 2:** Pneumonia classifier outputs probability (sigmoid, threshold 0.5)

---

## ⚠️ Disclaimer

> This application is for **educational and informational purposes only**.  
> It is **NOT** a substitute for professional medical diagnosis.  
> Always consult a qualified healthcare provider for medical decisions.  
> The AI predictions are based on a trained model and may not be 100% accurate.

---

<p align="center">Made with 🧠 by <strong>Aditya</strong></p>
