# Agent Context: Watabautet Monorepo

## Project Overview

Watabautet is a YouTube video summarization service. It uses a distributed architecture to handle long-running tasks (downloading and AI processing).

## System Architecture

The system follows a producer-consumer pattern:

- **Backend (FastAPI)**: Handles user requests, manages the database (PostgreSQL), and dispatches tasks.
- **Workers (Celery)**: Consumes tasks from RabbitMQ, interacts with external APIs (YouTube, Gemini), and stores results.
- **Infrastructure**:
  - **RabbitMQ**: Message broker for task distribution.
  - **Redis**: Result backend for Celery.
  - **PostgreSQL**: Persistent storage for users, videos, and summaries.

## Service Map

- `/backend`: API layer, authentication, and database management.
- `/workers`: Background processing logic (yt-dlp, Gemini integration).

## Development

- Development is carried out in Docker containers. Usually using the command `docker compose up --watch`.
- Local work with Python is done using uv commands (for example, to install packages or create a migration file).

### Security

- You are not allowed to read files with the .env extension.
