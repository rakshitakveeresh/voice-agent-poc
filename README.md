# Voice Agent POC

A Streamlit prototype for sending text or voice messages to an n8n customer-care
webhook. Voice conversations use the OpenAI API for speech transcription and
spoken replies.

## What you need

- Docker Desktop (recommended) or Docker Engine.
- An n8n instance with an active webhook workflow. The app does not start n8n
  for you.
- An OpenAI API key with access to the configured transcription and speech
  models if you want to use voice input or spoken replies. Text-only chat does
  not call OpenAI.
- (Optional) A PostgreSQL database with the customer table described below to
  use the **Human Overview** page.

## Run with Docker

These commands are run from the repository root.

### 1. Configure the app

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and set `N8N_WEBHOOK_URL` to your active n8n production webhook URL.
Set `OPENAI_API_KEY` if you intend to use voice features. Leave the webhook
username and password empty unless your webhook requires HTTP Basic
Authentication.

The `.env` file contains credentials. It is ignored by Git and excluded from the
Docker build context. Do not commit it, put secrets in the Dockerfile, or share
it.

### 2. Build the image

```bash
docker build --tag voice-agent-poc .
```

The Dockerfile pins the Python base image by digest and installs the exact
versions in [`requirements.lock`](./requirements.lock). To rebuild the same
dependency set later, build from the same repository revision and use the same
Docker platform. The lockfile records package versions, not package hashes.

### 3. Start the app

```bash
docker run --rm \
  --name voice-agent-poc \
  --publish 8501:8501 \
  --env-file .env \
  voice-agent-poc
```

Open [http://localhost:8501](http://localhost:8501). Keep the terminal open while
using the app; press `Ctrl+C` to stop it. The `--rm` option removes the stopped
container, but keeps the built image.

To run it in the background instead:

```bash
docker run --detach \
  --name voice-agent-poc \
  --publish 8501:8501 \
  --env-file .env \
  voice-agent-poc
```

Then view logs with `docker logs --follow voice-agent-poc` and stop it
with `docker stop voice-agent-poc`.

### 4. Check that it is responding

With the container running, check Streamlit's health endpoint:

```bash
curl --fail http://localhost:8501/_stcore/health
```

A healthy app returns `ok`. You can also open the browser URL above.

## Configuration

The Docker command passes values from `.env` into the container at runtime.
Alternatively, the app can read top-level values from
`.streamlit/secrets.toml`; do not commit a real secrets file.

| Variable | Required when | Description |
| --- | --- | --- |
| `N8N_WEBHOOK_URL` | Sending chat messages | Active n8n webhook endpoint. |
| `OPENAI_API_KEY` | Using voice input or spoken replies | OpenAI API key. |
| `N8N_USERNAME` | Webhook uses Basic Auth | Optional webhook username; set together with the password. |
| `N8N_PASSWORD` | Webhook uses Basic Auth | Optional webhook password; set together with the username. |
| `OPENAI_STT_MODEL` | Optional | Speech-to-text model; defaults to `gpt-4o-mini-transcribe`. |
| `OPENAI_TTS_MODEL` | Optional | Text-to-speech model; defaults to `gpt-4o-mini-tts`. |
| `DATABASE_URL` | Using Human Overview | Optional PostgreSQL connection URL. |

Vehicle ID and language are entered in the app's sidebar. The language defaults to
`en`.

### n8n webhook contract

The app sends a JSON `POST` request with this shape:

```json
{
  "text": "The customer's message",
  "language": "en",
  "session_id": "generated-session-id",
  "bmw_id": ""
}
```

Return a non-empty response body. For JSON responses, the app looks for reply
text in fields such as `output`, `reply`, `response`, `message`, `answer`, or
`text`. A plain-text response is also displayed directly.

## Voice input and browser access

Voice recording happens in the browser, while transcription and speech
generation happen in the app container via the OpenAI API. The browser must be
able to reach the app at `localhost:8501`. For access from another device, use
the host machine's reachable address and configure the browser and firewall
accordingly. Microphone access may require a secure browser context (HTTPS),
depending on the browser and device.

## Human Overview (optional)

The **Human Overview** page reads customer records from PostgreSQL. Configure
`DATABASE_URL` in `.env` with a connection URL, or set `POSTGRES_HOST`,
`POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` individually. The page
expects a `public.customers` table with at least `customer_id`, `name`, `email`,
`phone`, `preferred_language`, and `created_at`; it adds `customer_complaint`
and `processed` columns if they are missing.

Without a database connection, chat still works; the overview page reports that
database details are missing.

## Run locally (without Docker)

Use Python 3.11 and run the helper from the repository root:

```bash
./run.sh
```

On first run, `run.sh` creates a Python virtual environment, installs the pinned
dependencies from `requirements.lock`, and copies `.env.example` to `.env` if
you do not already have one. Edit `.env` with your webhook URL and credentials,
then run `./run.sh` again. The script starts Streamlit at
[http://localhost:8501](http://localhost:8501); press `Ctrl+C` to stop it.

To set up or start the app manually instead:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
cp .env.example .env
streamlit run app.py
```

On Windows, create the environment with `py -3.11 -m venv .venv`, activate it
with `.venv\Scripts\activate`, install `requirements.lock`, and run
`streamlit run app.py`.

## Troubleshooting

- **Docker cannot connect to the daemon:** Start Docker Desktop and wait for it
  to finish starting, then retry `docker build`.
- **Port 8501 is already in use:** Change the host side of the port mapping, for
  example `--publish 8502:8501`, then open `http://localhost:8502`.
- **Webhook errors:** Verify `N8N_WEBHOOK_URL`, that the n8n workflow is active,
  and that Basic Auth credentials are set if required.
- **Voice errors:** Verify `OPENAI_API_KEY` and that the account can use the
  selected models.
- **Human Overview says no database details were found:** Configure
  `DATABASE_URL` or the supported `POSTGRES_*` variables, then restart the app.

## Updating dependencies

[`requirements.txt`](./requirements.txt) lists the app's direct dependencies;
[`requirements.lock`](./requirements.lock) pins the tested dependency set used
for reproducible installs. When changing a dependency, update the lockfile,
test the Docker build and app, and commit both files together.
