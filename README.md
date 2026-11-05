# Voice Agent POC

This repository contains a voice-enabled customer-care prototype prepared for
project evaluation. It demonstrates a conversational frontend connected to an
AI workflow backend.

## What the project does

- **Frontend:** A Streamlit chat application with text and browser-recorded
  voice modes.
- **Backend:** n8n receives chat messages through a webhook and returns the
  agent response. The exported n8n workflows are in [`n8n/`](./n8n/).
- **Voice services:** OpenAI API speech-to-text and text-to-speech are used for
  voice conversations.
- **Optional customer overview:** A PostgreSQL-backed page can display and
  update customer complaint records when a database is configured.

The app does not run n8n or PostgreSQL for you. They must be available
separately. For voice features, configure an OpenAI API key.

## Architecture

See the architecture diagram in
[`Architecture/Voice_Agent_Architecture.drawio`](./Architecture/Voice_Agent_Architecture.drawio).
It describes the proposed Azure/private-network deployment and request flow.

## Prerequisites

- Git
- An active n8n instance
- Docker Desktop or Docker Engine **or** Python 3.11 for local setup
- An OpenAI API key for voice input/output

## Configure the environment

From the repository root, create a local environment file:

```bash
cp .env.example .env
```

Edit `.env` and set `N8N_WEBHOOK_URL` to the webhook URL for your active n8n
workflow. Set `OPENAI_API_KEY` to enable voice transcription and spoken
responses. Text chat does not call OpenAI. If the webhook requires HTTP Basic
Authentication, set both `N8N_USERNAME` and `N8N_PASSWORD`.

The `.env` file contains credentials. It is ignored by Git and excluded from
the Docker build context; never commit or share it.

### n8n setup

The n8n backend used by this project is hosted on a VPS and is not included in
this repository. The exported workflow JSON files in [`n8n/`](./n8n/) are
provided as architecture references to show how the workflow is organized;
they do not provide access to the live instance or its execution history.

The live n8n workflow execution will be shown during the project demo. To run
the prototype yourself, you need access to an active n8n instance with the
appropriate workflow, credentials, and connected services configured. Set its
webhook URL in `.env`.

The frontend sends a JSON `POST` containing `text`, `language`, `session_id`,
and `bmw_id`. The webhook should return a non-empty response. The app displays
plain-text responses or text from common JSON fields such as `output`, `reply`,
`response`, `message`, `answer`, or `text`.

## Run locally with Bash

On macOS or Linux, install Python 3.11, then run:

```bash
./run.sh
```

On first run, the script creates `.venv`, installs the pinned dependencies from
[`requirements.lock`](./requirements.lock), and creates `.env` from the example
if it does not exist. Add your n8n URL and credentials to `.env`, then run
`./run.sh` again. The app opens at [http://localhost:8501](http://localhost:8501).
Press `Ctrl+C` to stop it.

## Run with Docker

Start Docker Desktop or Docker Engine, then build the image from the repository
root:

```bash
docker build --tag voice-agent-poc .
```

Run the app, passing `.env` at runtime:

```bash
docker run --rm \
  --name voice-agent-poc \
  --publish 8501:8501 \
  --env-file .env \
  voice-agent-poc
```

Open [http://localhost:8501](http://localhost:8501). Press `Ctrl+C` to stop the
container. To verify it is healthy in another terminal:

```bash
curl --fail http://localhost:8501/_stcore/health
```

The image uses the pinned Python base image and dependencies in
`requirements.lock`. The `.env` file is passed only at runtime and is not
copied into the image.

## Optional PostgreSQL customer overview

The Human Overview page can connect to PostgreSQL using `DATABASE_URL` (or
supported `POSTGRES_*` / `DB_*` environment variables). The database and its
schema are not provisioned by the app. Chat can still be used without this
optional database.

## Azure infrastructure and CI/CD status

The [`terraform/`](./terraform/README.md) directory and
[`.github/workflows/terraform.yml`](./.github/workflows/terraform.yml) are
**drafts only**. They were added as a high-level starting point considering the
project timeline; Terraform resources, Azure authentication/state setup, and a
working deployment pipeline are not complete. Do not use them to deploy
infrastructure as-is. The n8n backend is external and is not provisioned by
Terraform.
