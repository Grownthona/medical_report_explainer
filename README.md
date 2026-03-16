# Medical Report Explainer 🏥🧪

An AI-powered system designed to transform complex medical reports into easy-to-understand explanations. This project leverages advanced OCR, NLP, and computer vision to analyze lab results, X-rays, and multi-patient documents, providing clear insights and voice explanations in multiple languages.

---

## 📸 Screenshots

### Upload Page

<img width="1920" height="1336" alt="Image" src="https://github-production-user-asset-6210df.s3.amazonaws.com/78976756/564061677-de059eed-860a-46ce-88ce-27a9bee3e4b8.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAVCODYLSA53PQK4ZA%2F20260316%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260316T101947Z&X-Amz-Expires=300&X-Amz-Signature=56f83ad167309b8057730c4bea3551e87476204cb61b17797f268f0940c105ec&X-Amz-SignedHeaders=host" />


### AI Report Analysis
<img width="1920" height="1932" alt="Image" src="https://github-production-user-asset-6210df.s3.amazonaws.com/78976756/564062071-d124bb27-e0d3-4d26-862a-206883dee574.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAVCODYLSA53PQK4ZA%2F20260316%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260316T102112Z&X-Amz-Expires=300&X-Amz-Signature=d18241c4caef9a6b9128882adbf0ccd4257c0684a352d020893e84ebcd10127a&X-Amz-SignedHeaders=host" />

### ChatBot Conversation
<img width="960" height="412" alt="Image" src="https://github-production-user-asset-6210df.s3.amazonaws.com/78976756/564062187-3b19d8de-a305-4545-9c4c-25594285f532.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAVCODYLSA53PQK4ZA%2F20260316%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260316T102135Z&X-Amz-Expires=300&X-Amz-Signature=5ee414f85d2802007f052d30d27452786174f88c587f619e895f7287ba71ded5&X-Amz-SignedHeaders=host" />

<img width="959" height="413" alt="Image" src="https://github-production-user-asset-6210df.s3.amazonaws.com/78976756/564062236-a9f721a0-f2e5-4119-88ff-f5d30a56409b.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAVCODYLSA53PQK4ZA%2F20260316%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260316T102206Z&X-Amz-Expires=300&X-Amz-Signature=bc39579e56a969b27e4903d71222dd672963b6190f40fcd30d53fd5dcd6884b9&X-Amz-SignedHeaders=host" />

---

## 🌟 Key Features

-   **Multi-Format OCR**: Extracts text from PDFs and images (JPG, PNG) using **Tesseract OCR**.
-   **Intelligent Analysis**:
    -   **Hybrid Pipeline**: High-accuracy deterministic extraction for **Lab Results** (Regex) combined with LLM-based insights for **Clinical/Imaging** reports.
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
-   **OCR**: [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
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
| `OPENAI_MODEL` | Specific OpenAI model (default: `gpt-4o-mini`). | Optional |
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
> On the first run, the backend will download models for X-ray analysis. Ensure Tesseract is installed on your host system if running locally.

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
