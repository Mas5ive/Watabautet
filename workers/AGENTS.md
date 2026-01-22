# Agent Context: Workers Service

## Role

Handles resource-intensive tasks: video metadata extraction, transcript fetching, and AI summarization.

## Key Components

- `app/tasks.py`: Implementation of Celery tasks.
- `app/celery.py`: Celery app configuration and `CustomTask` base class.
- `app/utils.py`: Helper functions for external API calls.

## External Integrations

- **yt-dlp**: Used for YouTube interaction. Highly unstable; check for updates if downloads fail.
- **Gemini API**: Used for content summarization. Requires `GOOGLE_API_KEY`.

## Error Handling & Retries

- **CustomTask**: Automatically retries on `DownloadError` (yt-dlp) and `RequestException`.
- **Backoff**: Uses exponential backoff with jitter, configurable via environment variables.

## Performance

- Workers are configured with `worker_prefetch_multiplier=1` to ensure fair task distribution for long-running AI jobs.
