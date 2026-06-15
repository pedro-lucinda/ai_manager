# Manager

FastAPI assistant that manages Gmail and Google Calendar through a single chat endpoint, powered by LangChain and OpenAI.

## Architecture

```text
FastAPI (app/main.py)
  ├── /health          health check
  └── /chat            assistant chat
        └── LangChain agent (app/agents/assistant.py)
              ├── Gmail toolkit (OAuth via token.json)
              └── Calendar toolkit (OAuth via token_calendar.json)
```

The assistant uses one LangChain agent with tools from both Google toolkits. OAuth credentials are loaded or obtained on first tool access and stored in local token files.

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) for dependency management
- Google Cloud project with Gmail API and Calendar API enabled
- OAuth 2.0 Desktop client credentials
- OpenAI API key

## Setup

1. Clone the repository and install dependencies:

```bash
uv sync
```

2. Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-openai-api-key
GMAIL_CLIENT_ID=your-google-client-id
GMAIL_CLIENT_SECRET=your-google-client-secret
GMAIL_OAUTH_PORT=8080
```

3. On first Gmail or Calendar tool use, complete the Google OAuth flow in your browser. Tokens are saved to `token.json` and `token_calendar.json` (gitignored).

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | — | OpenAI API key |
| `GMAIL_CLIENT_ID` | Yes | — | Google OAuth client ID |
| `GMAIL_CLIENT_SECRET` | Yes | — | Google OAuth client secret |
| `GMAIL_OAUTH_PORT` | No | `8080` | Local port for OAuth redirect |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model name |
| `OPENAI_TEMPERATURE` | No | `0` | Model temperature |
| `OPENAI_MAX_RETRIES` | No | `2` | Max OpenAI request retries |
| `GMAIL_SCOPES` | No | `https://mail.google.com/` | Comma-separated Gmail scopes |
| `GMAIL_TOKEN_FILE` | No | `token.json` | Path to Gmail token file |
| `CALENDAR_SCOPES` | No | `https://www.googleapis.com/auth/calendar` | Comma-separated Calendar scopes |
| `CALENDAR_TOKEN_FILE` | No | `token_calendar.json` | Path to Calendar token file |

## Run

```bash
fastapi dev app/main.py
```

The API is available at `http://127.0.0.1:8000`.

## Endpoints

### `GET /health/`

Health check.

**Response:** `{"status": "ok"}`

### `POST /chat`

Send a message to the assistant.

**Request body:**

```json
{
  "message": "What meetings do I have tomorrow?"
}
```

**Response:**

```json
{
  "reply": "..."
}
```

## Project structure

```text
app/
  config.py                 Settings and get_settings()
  main.py                   FastAPI application entry
  routers/
    health.py               Health endpoint
    assistant_chat.py       Chat endpoint
  agents/
    assistant.py            LangChain agent factory
    prompts.py              System prompt
    google_auth.py          Shared Google OAuth helper
    google_errors.py        Google error message mapping
    gmail/gmail.py
    calendar/calendar.py
```
