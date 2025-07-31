# AI Chatbot with Multi-Modal & Document Analysis

An end-to-end AI chatbot featuring real-time streaming conversations, document & image understanding, and a modern React frontend.

---

## Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Prerequisites](#prerequisites)
5. [Installation & Setup](#installation--setup)

   * [Backend (FastAPI)](#backend-fastapi)
   * [Frontend (React + Redux)](#frontend-react--redux)
6. [Configuration](#configuration)
7. [Usage](#usage)

   * [Running the Backend](#running-the-backend)
   * [Running the Frontend](#running-the-frontend)
8. [API Reference](#api-reference)
9. [Directory Structure](#directory-structure)
10. [Contributing](#contributing)
11. [License](#license)
12. [Resources & Acknowledgements](#resources--acknowledgements)

---

## Features

* **Streaming Chat**
  Real-time user ↔︎ assistant streaming via Server-Sent Events
* **Multi-Modal Support**
  Text, image, PDF, Word, CSV & JSON file understanding
* **Document Analysis**
  Instant summarization, table parsing, and content extraction
* **Vision Intelligence**
  Image captioning & object detection via Google Gemini API
* **Frontend UX**
  Markdown, code syntax highlighting, file previews, dark mode, copy/collapse controls

---

## Architecture

```
┌────────┐      HTTP      ┌─────────┐      gRPC/REST    ┌─────────────┐
│ Client │ ──────────── ▶ │ FastAPI │ ── ▶ Google Gemini API │
│ (React)│                │ Server  │                  │ AI Services  │
└────────┘                └─────────┘                  └─────────────┘
```

* **Client**

  * React + TypeScript
  * Redux Toolkit for state & streaming slices
  * Tailwind CSS for styling
* **Server**

  * FastAPI with CORS & SSE support
  * Pydantic schemas for request/response models
  * Google GenAI (Gemini) integration
  * StreamingResponse for real-time tokens

---

## Tech Stack

* **Backend**

  * Python 3.10+
  * FastAPI, Uvicorn
  * Pydantic
  * google-genai SDK
* **Frontend**

  * React 18, Next.js (app router)
  * TypeScript
  * Redux Toolkit
  * Tailwind CSS
  * react-markdown + prismjs

---

## Prerequisites

* Node.js 16+ & npm
* Python 3.10+
* Git
* Google Cloud account with Gemini API access

---

## Installation & Setup

### Backend (FastAPI)

1. Clone and enter server folder

   ```bash
   git clone <repo-url>
   cd <repo>/server
   ```
2. Create & activate virtual environment

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Mac/Linux
   .venv\Scripts\activate      # Windows
   ```
3. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```

### Frontend (React + Redux)

1. Navigate to client folder

   ```bash
   cd <repo>/client
   ```
2. Install dependencies

   ```bash
   npm install
   ```

---

## Configuration

Copy `.env.example` to `.env` in **server/** and set keys:

```dotenv
# server/.env
GEMINI_API_KEY=your_google_gemini_api_key
```

Optionally, in **client/** create `.env.local`:

```dotenv
# client/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

## Usage

### Running the Backend

```bash
# From server/
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

* Open Swagger UI:  `http://localhost:8000/docs`

### Running the Frontend

```bash
# From client/
npm run dev
```

* Visit  `http://localhost:3000`

---

## API Reference

### `POST /chat`

Start a streaming chat.

* **Request**: `ChatRequest`
* **Response**: **SSE** of `ChatResponse` tokens
* **Supports**: text + file attachments

### `POST /file/upload`

Upload a file for processing.

* **Request**: multipart `UploadFile`
* **Response**: `FileUploadResponse` (URL, mime type, size)

### `GET /models`

List available models & capabilities (`ModelInfo[]`)

### `GET /health`

Service health check `{status: "ok"}`

### `GET /`

Root endpoint: service metadata & features

---

## Directory Structure

```
.
├── client/                  # React frontend
│   ├── app/
│   │   ├── page.tsx
│   │   └── layout.tsx
│   ├── components/
│   │   ├── Chat.tsx
│   │   └── Sidebar.tsx
│   ├── store/
│   │   ├── chatSlice.ts
│   │   └── store.ts
│   ├── globals.css
│   └── package.json
└── server/                  # FastAPI backend
    ├── main.py
    ├── model.py
    ├── schemas.py
    ├── requirements.txt
    └── .env.example
```

---

## Contributing

1. Fork & clone
2. Create feature branch
3. Run tests & linters
4. Submit PR with clear description

Please follow [Conventional Commits](https://www.conventionalcommits.org/) and adhere to code style guidelines.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Resources & Acknowledgements

* [FastAPI Documentation](https://fastapi.tiangolo.com/)
* [Google Gemini API Reference](https://cloud.google.com/vertex-ai/docs/)
* [Redux Toolkit](https://redux-toolkit.js.org/)
* [Tailwind CSS](https://tailwindcss.com/)
* Inspired by modern AI chat platforms and best practices in frontend/backend design.
