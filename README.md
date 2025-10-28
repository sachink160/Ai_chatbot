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

- **Dynamic Prompts:**
  - Create reusable prompt templates with optional `gpt_model` selection
  - Upload documents and process them against an active prompt
  - Retrieve processed document results

- **News Agent:**
  - Fetches, summarizes, and delivers news headlines by category
  - Sends summaries to WhatsApp and logs to file

- **Social Media Monitoring:**
  - Telegram group link extraction and Excel logging

- **User Auth:**
  - Register, login, refresh, logout (JWT-based)

- **Subscriptions & Usage Limits:**
  - Plans with monthly limits (chats, documents, HR docs, video uploads, dynamic-prompt docs)
  - Endpoints to view plans, subscribe/cancel, and check current usage

- **API-first:**
  - RESTful endpoints for all features

- **Video to Audio Processing:**
  - Upload video files (mp4, mov, avi, mkv)
  - Automatically processes videos to generate 720p video and MP3 audio
  - User-specific file management: each user's uploads and processed files are isolated
  - List uploaded and processed files per user
  - Download processed files securely (only the owner can access)
  - Optimized with background thread processing for fast, non-blocking uploads

- **Logging & Monitoring:**
  - Centralized JSON logging for app, errors, and access
  - Middleware for request/response timing and global error handling
  - Endpoints to fetch logs, errors, access logs, and summary analytics

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

## 🧩 Dynamic Prompts Functionality

- **Manage Prompts:**
  - `POST /dynamic-prompts/` — Create a prompt (name, description, template, optional `gpt_model`)
  - `GET /dynamic-prompts/` — List prompts (supports deployments without `gpt_model` column)
  - `GET /dynamic-prompts/{prompt_id}` — Get a prompt
  - `PUT /dynamic-prompts/{prompt_id}` — Update a prompt
  - `DELETE /dynamic-prompts/{prompt_id}` — Delete a prompt

- **Process Documents:**
  - `POST /dynamic-prompts/upload-document` — Upload a document and process with an active prompt
  - `GET /dynamic-prompts/processed-documents/` — List processed documents
  - `GET /dynamic-prompts/processed-documents/{document_id}` — Get processed doc metadata
  - `GET /dynamic-prompts/processed-documents/{document_id}/result` — Get processing result JSON

Limits are enforced via subscription (see below).

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

## 🗄️ Database Migrations (Alembic)

This project uses Alembic for database schema management. The setup is configured to automatically detect model changes and generate migrations.

### Quick Start

```bash
# Check current migration status
alembic current

# Create a new migration from model changes
alembic revision --autogenerate -m "description of changes"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

### Using the Helper Script

```bash
# Check status
python alembic_helpers.py status

# Create and apply migration
python alembic_helpers.py autogenerate "add new feature"
python alembic_helpers.py upgrade

# Rollback
python alembic_helpers.py downgrade -1
```

### Documentation

- **[ALEMBIC_GUIDE.md](ALEMBIC_GUIDE.md)** - Comprehensive guide to database migrations
- **[ALEMBIC_QUICK_REF.md](ALEMBIC_QUICK_REF.md)** - Quick reference for common commands

The Alembic setup includes:
- ✅ Automatic model detection
- ✅ Database URL from environment variables
- ✅ Safe migration handling
- ✅ SQLite and PostgreSQL compatibility
- ✅ Helper scripts for common tasks

---

## 🛠️ Usage

### API Endpoints (Main)

#### Auth
- `POST /register` — Register new user
- `POST /login` — Login, get JWT tokens
- `POST /refresh` — Refresh JWT
- `POST /logout` — Logout, blacklist token
- `GET /profile` — Get user profile, subscription and usage summary
- `PUT /profile` — Update profile (fullname, email, phone, password)

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

#### Dynamic Prompts
- `POST /dynamic-prompts/` — Create prompt
- `GET /dynamic-prompts/` — List prompts
- `GET /dynamic-prompts/{prompt_id}` — Get prompt
- `PUT /dynamic-prompts/{prompt_id}` — Update prompt
- `DELETE /dynamic-prompts/{prompt_id}` — Delete prompt
- `POST /dynamic-prompts/upload-document` — Upload and process a document with a prompt
- `GET /dynamic-prompts/processed-documents/` — List processed docs
- `GET /dynamic-prompts/processed-documents/{document_id}` — Get processed doc
- `GET /dynamic-prompts/processed-documents/{document_id}/result` — Get processing result

#### Subscriptions & Usage
- `GET /plans` — List active plans
- `POST /subscribe` — Subscribe to a plan (simplified)
- `POST /cancel` — Cancel current subscription
- `GET /user/subscription` — Current subscription
- `GET /user/subscription/history` — Subscription history
- `GET /user/usage` — Current usage and plan limits

#### Logs Management
- `GET /logs/app` — App logs (filters: lines, level, start_time, end_time)
- `GET /logs/errors` — Error logs (filters: lines, start_time, end_time)
- `GET /logs/access` — Access logs (filters: lines, start_time, end_time)
- `GET /logs/summary` — Summary across logs for last N hours
- `GET /logs/files` — File sizes and modified times
- `POST /logs/test` — Emit a test log at a level

---

## 🧠 Extending & Customization
- Add new tools in `app/Agent/tools.py`
- Add new API endpoints in `app/routes/`
- Integrate new LLMs or vector DBs as needed

---

## ⚙️ Middleware & Scheduling
- Logging middleware tracks method, path, user, status, and response time; slow requests (>5s) are flagged
- Error handling middleware captures context and logs structured errors
- News agent job is scheduled every 10 hours via APScheduler on app startup
- CORS is enabled for all origins by default; adjust in `app.main`

---

## 🔐 Environment Variables
Create a `.env` or provide via environment:

- `DATABASE_URL` — SQLAlchemy connection string
- `SECRET_KEY` — JWT secret
- `OPENAI_API_KEY` — For LLM operations (RAG, Dynamic Prompts, Chat)

Optional: tweak limits or plan initialization via service layer.

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