# SENTRY_OS (Local SOAR System)

SENTRY_OS is an AI-powered local Security Orchestration, Automation, and Response (SOAR) platform. Designed with a sleek, cyberpunk-inspired terminal aesthetic, it provides real-time threat analysis, network monitoring, and rapid human-in-the-loop incident response directly via Telegram.

## 🚀 Key Features

- **AI-Driven Threat Analysis**: Integrates with the **Groq API (LLaMA 3.1)** to automatically parse incoming security payloads. It identifies severity levels, maps threats to **MITRE ATT&CK** tactics, and provides predictive hardening recommendations.
- **Real-Time Threat Dashboard**: A lightweight, dependency-free frontend (Vanilla HTML, JS, and Tailwind CSS) featuring a zero-refresh architecture. It polls the backend to display real-time system health, live metrics, and animated threat logs.
- **Telegram Incident Response**: Alerts are instantly forwarded to a configured Telegram chat. Security operators can take immediate action using inline buttons to **[Isolate Host]** or **[Ignore]** threats directly from their mobile devices.
- **Deduplication Engine**: Built-in logic to prevent alert fatigue by ignoring redundant incoming payloads from the same source over a specified time window.
- **Local Data Storage**: Uses a lightweight local SQLite database to persist alerts, raw payloads, AI responses, and human actions.

---

## 🏗️ Architecture & Stack

- **Backend:** Python, FastAPI, Uvicorn, SQLite, HTTPX
- **Frontend:** Vanilla HTML5, JavaScript, TailwindCSS (via CDN)
- **AI Integration:** Groq Python SDK (LLaMA 3.1 8B Instant)
- **Notifications:** Telegram Bot API

---

## 🛠️ Getting Started

### 1. Prerequisites

- Python 3.9+
- A [Groq API Key](https://console.groq.com/keys)
- A [Telegram Bot Token](https://core.telegram.org/bots#how-do-i-create-a-bot) & Chat ID

### 2. Installation

Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/BitlaUmesh/SENTRY.git
cd SENTRY

# Create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install fastapi uvicorn groq python-dotenv httpx
```

### 3. Configuration

Create a `.env` file in the root directory of the project and add your API keys:

```env
GROQ_API_KEY=gsk_your_groq_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
```

### 4. Running the Application

**Start the Backend Engine:**

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
```
*The SQLite database (`sentry.db`) will initialize automatically on startup.*

**Launch the Dashboard:**

Simply open `frontend/index.html` in your preferred modern web browser. 

---

## 🧪 Testing & Demonstration

To see SENTRY_OS in action without waiting for real alerts, you can use the included demographic seeding scripts:

- **Seed Demo Alerts:** 
  ```bash
  python scripts/seed_demo.py
  ```
  *This script will simulate incoming payloads, triggering the Groq AI analysis and populating your dashboard and Telegram chat.*

- **Reset Database:**
  ```bash
  python scripts/nuke_db.py
  ```
  *Wipes all current alerts to start fresh.*

---

## 📡 API Endpoints

- `POST /api/v1/alert` - Ingests a new security payload for AI analysis.
- `GET /api/v1/alerts` - Fetches the latest 50 security alerts (used by the frontend dashboard).
- `POST /api/v1/telegram-webhook` - Processes incoming callback queries (Isolate/Ignore) from the Telegram bot.

---

## 🛡️ License & Disclaimer

SENTRY_OS is developed for educational and demonstration purposes. Ensure you have proper authorization before deploying automated containment or isolation actions in a production environment.
