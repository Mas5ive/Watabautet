# Agent Context: Backend Service

## Role

The entry point for all client interactions. It manages state and orchestrates background work.

## Key Components

- `app/api/routes/`: Contains endpoint definitions.
- `app/models.py`: SQLAlchemy models (Postgres).
- `app/crud.py`: Centralized database operations. **Always use this layer for DB access.**
- `app/core/config.py`: Centralized settings management.

## Development Patterns

- **Dependency Injection**: Use `app/api/deps.py` for database sessions and user authentication.
- **Migrations**: Managed by Alembic. New models or changes require a new script in `app/alembic/versions/`.
- **Task Dispatching**: Tasks are sent to Celery using `app.state.celery.send_task()`.
