# Medical Report Explainer 🏥🧪

An AI-powered system designed to transform complex medical reports into easy-to-understand explanations. This project leverages advanced OCR, NLP, and computer vision to analyze lab results, X-rays, and multi-patient documents, providing clear insights and voice explanations in multiple languages.

---

## 📸 Screenshots

### Upload Page
<div align="center">
<img src="https://github.com/user-attachments/assets/a1bd996e-7903-4f36-8373-f3b93e43fea5" width="48%" />
<img src="https://github.com/user-attachments/assets/6e92691b-2264-4acf-aeda-342856dd3a0c" width="48%" />
</div>

### AI Report Analysis
<div align="center">
<img src="https://github.com/user-attachments/assets/8c2a9f2d-4b34-485f-a7bb-1ba17d6662b2" width="30%" />
<img src="https://github.com/user-attachments/assets/7a9f3885-7d82-449a-a36e-4cd500fd9e4f" width="33%" />
<img src="https://github.com/user-attachments/assets/82360010-bfda-4b8f-ba62-1469b45c8cd0" width="33%" />
</div>

### ChatBot Conversation
<div align="center">
<img src="https://github.com/user-attachments/assets/c18b8d62-8517-4d6e-a4f3-e5bc4a9dddcc" width="48%" />
<img src="https://github.com/user-attachments/assets/adaf9481-a380-4469-9968-640d433f514f" width="48%" />
</div>

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
    -   **ChatBot (Graph RAG)**: 
        -   **MediBot**: Uses a Graph-based Retrieval-Augmented Generation (RAG) system to navigate report structures.
        -   **Web Enrichment**: Automatically fetches trusted medical definitions from **NIH MedlinePlus** for abnormal results.
        -   **Multi-Patient Aware**: Remembers and distinguishes between different patients in a single conversation.
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

## ⚙️ Configuration & Environment Variables

Create a `.env` file in the root directory (based on `.env.example`):

| Variable | Description | Required |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` | Your OpenAI API key for report analysis. | Yes |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to Google Cloud JSON key (for Text-to-Speech). | Optional |
| `CORS_ORIGINS` | Comma-separated list of allowed origins. | Optional |
| `VITE_API_BASE` | URL of the backend API (used during frontend build). | Optional |

---

## 🚀 Getting Started

### Prerequisites
-   **Python 3.10**
-   **Node.js** (v18 or higher)
-   **Tesseract OCR** (Required for some fallback paths)

### Docker Deployment (Recommended)
The easiest way to run the entire application is using Docker Compose.

1.  **Configure environment**:
    ```bash
    cp .env.example .env
    # Edit .env and add your OPENAI_API_KEY
    ```
2.  **Build and Run**:
    ```bash
    docker compose up --build -d
    ```
3.  **Access the application**:
    - **Frontend:** `http://localhost`
    - **Backend API:** `http://localhost:8000`

> [!NOTE]
> On the first run, the backend will download several gigabytes of models for OCR (PaddleOCR) and X-ray analysis. This may take some time depending on your internet connection.

### Local Development Setup

#### Backend Setup
1.  Navigate to `medical_ai`:
    ```bash
    cd medical_ai
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    ```
2.  Run the server:
    ```bash
    fastapi dev app/main.py
    ```

#### Frontend Setup
1.  Navigate to `frontend`:
    ```bash
    cd frontend
    npm install
    ```
2.  Run the development server:
    ```bash
    npm run dev
    ```
    The application will be available at `http://localhost:5173`.

---

## 🔌 API Summary

-   `POST /extract/file`: Upload one or more medical report files (PDF/Images). Handles OCR → Analysis or X-ray classification.
-   `POST /extract/text`: Direct submission of raw report text for analysis.
-   `POST /tts`: Convert text to speech.
-   `POST /chat`: Interactive MediBot.
-   `GET /`: Health check and service metadata.

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
