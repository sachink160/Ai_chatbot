# Multi_tool_chatbot

A modular, AI-powered platform for document analysis, HR tools, news summarization, social media monitoring, and more. Built with FastAPI, LangChain, LlamaIndex, and modern AI/LLM integrations.

---

## 🚀 Overview

**Multi_tool_chatbot** is a backend system that provides:
- Document Q&A and summarization (RAG, HR, legal, etc.)
- AI-powered chat and tools (search, trip planning, weather, YouTube, etc.)
- Automated news summarization and WhatsApp delivery
- Social media (Telegram) link monitoring
- User authentication and management
- Modular, extensible architecture

---

## 🧩 Features

- **Document Q&A (RAG):**
  - Upload documents (PDF, text)
  - Ask questions, extract summaries, action items, or legal issues
  - Uses LlamaIndex, LangChain, and OpenAI/LLM models

- **HR Document Tools:**
  - Upload, activate/deactivate, and query HR documents
  - Summarization and Q&A for HR compliance

- **AI Chatbot & Tools:**
  - General chat, Google/Wikipedia search, trip planner, weather, YouTube summarizer, email, and more
  - Modular tool system (see `app/Agent/tools.py`)

- **News Agent:**
  - Fetches, summarizes, and delivers news headlines by category
  - Sends summaries to WhatsApp and logs to file

- **Social Media Monitoring:**
  - Telegram group link extraction and Excel logging

- **User Auth:**
  - Register, login, refresh, logout (JWT-based)

- **API-first:**
  - RESTful endpoints for all features

- **Video to Audio Processing:**
  - Upload video files (mp4, mov, avi, mkv)
  - Automatically processes videos to generate 720p video and MP3 audio
  - User-specific file management: each user's uploads and processed files are isolated
  - List uploaded and processed files per user
  - Download processed files securely (only the owner can access)
  - Optimized with background thread processing for fast, non-blocking uploads

---

## 🎬 Video to Audio Functionality

This project includes a robust video-to-audio feature:

- **Upload Video:**
  - Endpoint: `POST /video-to-audio/upload`
  - Accepts video files (mp4, mov, avi, mkv)
  - Processes the video to create a 720p version and extract audio as MP3
  - Processing is performed in a background thread for optimal performance
  - Files are stored in user-specific directories

- **List Uploaded Files:**
  - Endpoint: `GET /video-to-audio/uploads`
  - Returns a list of the current user's uploaded video files

- **List Processed Files:**
  - Endpoint: `GET /video-to-audio/processed`
  - Returns a list of the current user's processed video and audio files

- **Download Processed Files:**
  - Endpoint: `GET /video-to-audio/download/{user_id}/{filename}`
  - Only the authenticated user can download their own processed files

---

## 📁 Project Structure

```
Multi_tool_chatbot/
├── app/
│   ├── Agent/           # AI tools, news, HR, RAG, social media agents
│   ├── routes/          # FastAPI route modules (API endpoints)
│   ├── Food/            # (Placeholder for food-related features)
│   ├── compressdocs/    # (Reserved for document compression)
│   ├── main.py          # FastAPI app entrypoint
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic schemas
│   ├── auth.py          # Auth logic
│   ├── utils.py         # Utility functions
│   ├── config.py, settings.py, database.py
├── docs/                # Uploaded/processed documents
├── hr_docs/             # HR document uploads
├── storage/             # Social media Excel logs, etc.
├── uploads/             # (General uploads)
├── processed/           # (Processed video/audio files)
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker build
├── docker-compose.yml   # Multi-container setup (app + nginx)
├── nginx.conf           # Nginx reverse proxy config
├── README.md            # (This file)
```

---

## ⚙️ Installation

### Prerequisites
- Python 3.11+
- (Optional) Docker & Docker Compose

### Local Setup
```bash
# Clone the repo
$ git clone <repo-url>
$ cd Multi_tool_chatbot

# Create virtual environment
$ python -m venv .venv
$ source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
$ pip install --upgrade pip
$ pip install -r requirements.txt

# Set up environment variables (see .env.example or docs)
$ cp .env.example .env  # Edit as needed

# Run the app
$ uvicorn app.main:app --reload
```

### Docker Setup
```bash
# Build and run with Docker Compose
$ docker-compose up --build
```
- App runs on [http://localhost:8000](http://localhost:8000)
- Nginx reverse proxy on [http://localhost/](http://localhost/)

---

## 🛠️ Usage

### API Endpoints (Main)

#### Auth
- `POST /register` — Register new user
- `POST /login` — Login, get JWT tokens
- `POST /refresh` — Refresh JWT
- `POST /logout` — Logout, blacklist token

#### Document Q&A (RAG)
- `POST /upload` — Upload document
- `GET /documents` — List user documents
- `POST /ask` — Ask question about a document (summarize, extract issues, etc.)

#### HR Tools
- `POST /hr/upload` — Upload HR document
- `GET /hr/documents` — List HR docs
- `POST /hr/documents/{doc_id}/activate` — Activate doc
- `POST /hr/documents/{doc_id}/deactivate` — Deactivate doc
- `POST /hr/ask` — Ask question about active HR doc

#### AI Chatbot & Tools
- `POST /chat` — General chat, tool invocation
- `GET /chat/history` — Get chat history

#### News Agent
- Automated, runs on schedule (see logs/WhatsApp)

#### Social Media
- (Telegram listener, see code for activation)

#### Video to Audio
- `POST /video-to-audio/upload` — Upload and process a video file
- `GET /video-to-audio/uploads` — List uploaded video files (per user)
- `GET /video-to-audio/processed` — List processed video/audio files (per user)
- `GET /video-to-audio/download/{user_id}/{filename}` — Download a processed file (user only)

---

## 🧠 Extending & Customization
- Add new tools in `app/Agent/tools.py`
- Add new API endpoints in `app/routes/`
- Integrate new LLMs or vector DBs as needed

---

## 📝 License
Specify your license here (MIT, Apache, etc.)

---

## 🙏 Acknowledgements
- [FastAPI](https://fastapi.tiangolo.com/)
- [LangChain](https://www.langchain.com/)
- [LlamaIndex](https://www.llamaindex.ai/)
- [OpenAI](https://openai.com/)
- [APScheduler](https://apscheduler.readthedocs.io/)
- [Telethon](https://docs.telethon.dev/)
- [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) 