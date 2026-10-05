# 🤖 Bettina AI — WhatsApp Conversational Agent for Healthcare & Wellness

Automated AI agent developed with Python and Flask, integrated with Evolution API and OpenAI (GPT-4o / Whisper) for automated patient qualification, triage, and scheduling in wellness clinics and Pilates studios.

## 🚀 Key Features
- **Conversational Triage:** Natural language understanding for clinical complaints and services.
- **Human Handover:** Automatic pausing when a human attendant intervenes.
- **Multimodal Support:** Voice audio transcription using OpenAI Whisper.
- **Automated Follow-ups:** Re-engagement sequences for pending inquiries.

## 🛠️ Tech Stack & Infrastructure
- **Backend:** Python 3.11, Flask
- **Database:** SQLite (persisted via Docker Volumes)
- **Containerization & Deployment:** Docker, VPS Linux, Easypanel / Cloudflare
- **APIs:** Evolution API (WhatsApp), OpenAI API
