# PRJ-256: AI-Based Sentiment Analysis of Incoming Helpdesk Calls

## 1. Project Overview & Problem Statement
Helpdesk teams handle high volumes of customer support call recordings daily. Manually reviewing these calls to evaluate customer satisfaction is time-consuming and unscalable. 

This project solves this by introducing a complete, functional, demonstrable pipeline that converts **helpdesk call recordings -> text transcripts -> sentiment classes -> issue topics -> priority alerts**. It aggregates these structured data insights into an interactive analytics dashboard for team supervisors.

Key analytical questions answered:
* What is the distribution of positive, neutral, and negative customer call sentiments?
* Which call logs require immediate supervisor callback?
* What are the most common helpdesk issues driving negative customer sentiment?
* How is helpdesk sentiment shifting over time?

---

## 2. Core Architecture & Pipeline Flow
The system processes calls through the following sequential pipeline:
1. **Audio Input**: Customer uploads recording file (`.wav`, `.mp3`, `.m4a`).
2. **Speech-to-Text**: Transcribes audio content utilizing **OpenAI Whisper**.
3. **Sentiment Analysis**: Evaluates customer attitude classes utilizing a fine-tuned **DistilBERT** multiclass model.
4. **Issue Classification**: Pinpoints helpdesk topics (Billing, Refund, Delivery, etc.) from transcript vocabulary.
5. **Priority Scoring**: Combines sentiment confidence and topic risk (e.g., negative refund requests) to assign priority flags (`HIGH`, `MEDIUM`, `NORMAL`).
6. **Persistence**: Saves records in **MongoDB**.
7. **Analytics**: Aggregates database state into interactive dashboard charts.

---

## 3. Technology Stack
* **Frontend**: React.js (Vite), Tailwind CSS, Recharts, Lucide Icons.
* **Backend**: Python (FastAPI), Pydantic, Motor (Async MongoDB), PyTest.
* **Database**: MongoDB Server (running locally on port 27017).
* **AI Engine**: `openai-whisper` (STT), Hugging Face `transformers` (Sentiment DistilBERT).

---

## 4. Folder Structure
```text
helpdesk-sentiment/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── calls.py              # Routes: upload, process, search, history
│   │   │   └── dashboard.py          # Routes: charts, summary numbers, trends
│   │   ├── core/
│   │   │   ├── config.py             # Config & settings loaders
│   │   │   └── database.py           # MongoDB lifecycle driver client
│   │   ├── schemas/
│   │   │   ├── call.py               # Call validation models
│   │   │   └── dashboard.py          # Dashboard aggregation schemas
│   │   ├── services/
│   │   │   ├── speech_to_text.py     # Whisper audio transcriber (with Mock fallback)
│   │   │   ├── sentiment.py          # DistilBERT sentiment engine (with Mock fallback)
│   │   │   ├── issue_detection.py    # Rule-based helpdesk topic detector
│   │   │   └── priority.py           # Threshold rules escalations calculator
│   │   ├── utils/
│   │   │   └── file_handler.py       # Audio files validator & length estimator
│   │   ├── main.py                   # FastAPI app entry point
│   │   └── setup_db.py               # Database seeder script
│   ├── .env.example
│   ├── requirements.txt
│   └── run.py                        # Uvicorn boot helper
├── frontend/
│   ├── src/
│   │   ├── components/               # Sidebar, Navbar UI wrappers
│   │   ├── pages/                    # Dashboard, Upload, History, Details, Priority
│   │   ├── services/                 # api.js fetch client with progress upload
│   │   ├── utils/                    # formatting converters
│   │   └── App.jsx                   # View Router & health polling
│   ├── package.json
│   └── tailwind.config.js
├── data/
│   └── uploads/                      # Storage folder for uploads
├── README.md
└── .gitignore
```

---

## 5. Setup & Installation

### Step 1: Clone & Configure Workspace
Open terminal in the project root:
```bash
# Verify MongoDB is running locally
# By default, MongoDB is expected at mongodb://localhost:27017
```

### Step 2: Backend Setup
Create and launch the virtual environment inside `backend/`:
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Run Database Seeder
Seed MongoDB with mock call history to instantly populate charts:
```bash
python app/setup_db.py
```

### Step 4: Start Backend server
```bash
python run.py
# Server starts running at http://127.0.0.1:8000
```

### Step 5: Frontend Setup
Open a separate terminal window and launch the Vite development server:
```bash
cd frontend
npm install
npm run dev
# React app starts running at http://localhost:5173
```

---

## 6. AI Model Setup & Configuration
By default, the application runs with **`USE_MOCK_AI=true`** enabled in `.env`. This utilizes a robust, deterministic heuristics engine to analyze uploads, enabling instant local demonstrations without downloading huge PyTorch dependencies (~2.5GB).

To run live neural network models locally:
1. Ensure `ffmpeg` is installed on your system path.
2. Edit `.env` and set:
   ```env
   USE_MOCK_AI=false
   ```
3. Boot the backend; it will automatically download Whisper (tiny model, ~70MB) and DistilBERT (~268MB) and run local inference on CPU.

---

## 7. Troubleshooting Windows Long Paths (WinError 206)
During package installation, if pip throws `WinError 206: The filename or extension is too long` while installing PyTorch, this is a standard Windows file-path length limitation (260 chars).
* **Fix**: Run PowerShell as Administrator and run the command:
  ```powershell
  New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
  ```
  Then restart your terminal and re-run `pip install -r requirements.txt`.
