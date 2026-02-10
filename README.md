# Watabautet

## Description

Watabautet is a web application that provides users with the ability to extract summarised content from YouTube videos. It features a user-friendly frontend interface built with React and TypeScript. To generate the summary, a machine learning model, Gemini, is used, which is accessed via the API. The main use of the app is to speed up information retrieval from long videos, with the ability to save and organise the extracted summaries for future use.

### Available features

1. Translation of any video into any language
2. 3 types of summaries to choose from (short, medium, detailed)
3. Saving of summarization results in the user's personal library

### Technical features

>**The project deliberately uses overengineering!**

Technologies:

Backend:

- python 3.13
- fastapi
- postgres
- celery

Frontend:

- react
- typescript
- vite
- tailwindcss

Infrastructure:

- docker
- uv
- rabbitmq
- redis

The tests are mainly written for the backend service in a mixed style.

### Performance

The workers service depends on **yt-dlp** and the **Gemini** model. These components are highly unstable. If the service is experiencing problems because of them, your first step is to update their versions. This will most likely help.

## Install

```bash
git clone https://github.com/Mas5ive/Watabautet.git
```

```bash
cd Watabautet
```

Create your own *.env* files based on *.env.example* in some directories. To use Gemini, you need to create your own API key:

```bash
# Google
GOOGLE_API_KEY="your-key"
...
```

## Development

The project is developed in Docker containers using **Vscode**, so you will see the configuration for debugging in this IDE. I also recommend creating a workspace configuration file to make it easier to work in multiple virtual environments (backend and workers are separate services). Name it, for example, *watabautet.code-workspace* and enter:

```bash
{
  "folders": [
    {
      "name": "root",
      "path": "."
    },
    {
      "name": "backend",
      "path": "backend"
    },
    {
      "name": "workers",
      "path": "workers"
    },
    {
      "name": "frontend",
      "path": "frontend"
    }
  ],
  "settings": {
    "files.exclude": {
      "workers/": true,
      "backend/": true,
      "frontend/": true,
      "**/.venv": true,
      "**/__pycache__": true,
      "node_modules": true
    },
  }
}
```

To create virtual environments for services, navigate to directories containing the *uv.lock* files and execute the command:

```bash
uv sync --locked --group dev
```

Now everything is ready! Run the command from the project root directory to start the application:

```bash
docker compose up --build --watch
```

After a while, the celery service will start. Once it successfully connects to the rabbitmq service and stops displaying information, you can start working.

- <http://127.0.0.1:8000/docs> - address for interacting with the API.
- <http://127.0.0.1:3000> - address for the web interface.
- <http://127.0.0.1:15672/> - address for the RabbitMQ access panel (default username is admin, password is 0000)

See the *docker-compose.override.yml* file for available ports to other services.

To stop the application, press **Ctrl+C** in the terminal. If you need to delete the Docker containers along with all data, run the command:

```bash
docker compose down -v
```
