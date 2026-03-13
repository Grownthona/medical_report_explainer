# Medical Report Explainer 🏥🧪

An AI-powered system designed to transform complex medical reports into easy-to-understand explanations. This project leverages advanced OCR, NLP, and computer vision to analyze lab results, X-rays, and multi-patient documents, providing clear insights and voice explanations in multiple languages.

---

## 🌟 Key Features

-   **Multi-Format OCR**: Extracts text from PDFs and images (JPG, PNG) using **PaddleOCR**.
-   **Intelligent Analysis**:
    -   **NER / LLM Pipeline**: Specifically tuned for medical reports.
    -   **Lab Result Extraction**: Accurate extraction of test names, values, units, and status (Normal/High/Low).
    -   **Report Categorization**: Automatically identifies report types (Hematology, Biochemistry, etc.).
-   **X-Ray Vision**: Dedicated analysis for X-ray images using **TorchXrayVision**, providing findings and advice.
-   **Multi-Patient Support**: Handles multi-page documents containing reports for different patients automatically.
-   **Multi-Language Explanations**: Supports **English, Bengali (BN), Arabic (AR), Hindi (HI), and Urdu (UR)**.
-   **Interactive Components**:
    -   **ChatBot**: Get immediate answers about your medical findings.
    -   **Voice Explainer**: Listen to the report summary and test explanations.
-   **Modern UI**: Sleek, responsive frontend built with **React** and **Vite**.

---

## 🛠️ Tech Stack

### Backend (`medical_ai`)
-   **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
-   **OCR**: [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
-   **NLP**: [spaCy](https://spacy.io/)
-   **Explaining/Extraction**: LLM-based processing (pipeline-ready)
-   **X-Ray Analysis**: [TorchXrayVision](https://github.com/mlmed/torchxrayvision), PyTorch
-   **Document Handling**: `pdfplumber`, `pdf2image`, `OpenCV`

### Frontend (`frontend`)
-   **Framework**: [React 19](https://react.dev/)
-   **Build Tool**: [Vite](https://vitejs.dev/)
-   **Styling**: Vanilla CSS (Modern design)
-   **API Client**: [Axios](https://axios-http.com/)
-   **Routing**: [React Router 7](https://reactrouter.com/)

---

## 📂 Project Structure

```text
.
├── frontend/             # React/Vite web application
│   ├── src/
│   │   ├── components/   # Reusable UI elements (ChatBot, DropZone, etc.)
│   │   ├── pages/        # Main views (Home, Upload, Results)
│   │   └── data/         # Mock data for testing
│   └── package.json
└── medical_ai/           # FastAPI backend & AI services
    ├── app/
    │   ├── main.py       # API entry point & routes
    │   ├── services/     # Core logic (OCR, Assembler, X-ray)
    │   └── models/       # Data schemas
    └── requirements.txt
```

---

## 🚀 Getting Started

### Prerequisites
-   **Python 3.10**
-   **Node.js** (v18 or higher)
-   **Tesseract OCR** (Required for some fallback paths)

### Backend Setup
1.  Navigate to the backend directory:
    ```bash
    cd medical_ai
    ```
2.  Create and activate a virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Run the server:
    ```bash
    fastapi dev app/main.py
    ```
    The API will be available at `http://localhost:8000`.

### Frontend Setup
1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Run the development server:
    ```bash
    npm run dev
    ```
    The application will be available at `http://localhost:5173`.

---

## 🔌 API Summary

-   `POST /extract/file`: Upload one or more medical report files (PDF/Images). Handles OCR → Analysis or X-ray classification.
-   `POST /extract/text`: Direct submission of raw report text for analysis.
-   `GET /`: Health check and service metadata.

---

## 📄 License
*Specify license here (e.g., MIT).*
