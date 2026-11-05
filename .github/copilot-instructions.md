# Voice Agent POC: Copilot Instructions

## Project overview

This repository contains a Streamlit prototype for customer-care conversations.
The app sends text messages to an externally hosted n8n webhook, supports
browser-recorded voice input, and uses OpenAI for transcription and spoken
replies. PostgreSQL-backed customer records are optional.

For setup and user-facing instructions, see the repository [README](../README.md).

## Repository map

- `app.py` is the Streamlit chat entry point and contains webhook, audio, and
  conversation handling.
- `pages/human_overview.py` implements the optional PostgreSQL-backed Human
  Overview page.
- `main.py` is a standalone database connection script; it is not the app
  entry point.
- `run.sh` creates/uses `.venv`, installs `requirements.lock`, creates `.env`
  from the example if needed, and launches Streamlit.
- `Dockerfile` builds the app image. Docker runs `app.py` and includes
  `pages/`.
- `requirements.txt` lists direct dependency ranges. `requirements.lock` pins
  the tested versions and is used by both `run.sh` and Docker builds.
- `Architecture/` contains the project architecture diagram.
- `terraform/` contains a TODO-only Azure infrastructure layout; it does not
  contain deployable Terraform resources yet.
- `.github/workflows/terraform.yml` is a manual/PR Terraform workflow draft. It
  skips cloud actions until root Terraform files and Azure configuration exist.

## Working in this repository

- Keep changes focused and follow the existing Python and Streamlit patterns.
- Keep `README.md`, `.env.example`, and `.streamlit/secrets.toml.example`
  aligned when configuration or setup requirements change.
- Never add real API keys, webhook credentials, database passwords, `.env`, or
  `.streamlit/secrets.toml` to source control. Use the example files for
  placeholders and pass secrets at runtime.
- The n8n service is external; this repository does not run or configure it.
  The app sends `text`, `language`, `session_id`, and `bmw_id` in a JSON POST.
- Keep voice transcription and TTS model defaults consistent with the
  `OPENAI_STT_MODEL` and `OPENAI_TTS_MODEL` settings documented in the README.
- Treat the Human Overview database integration as optional. Preserve chat
  functionality when PostgreSQL is not configured.
- When changing dependencies, update `requirements.txt` and regenerate or
  validate `requirements.lock`; test the Docker build.
- Do not describe the Azure infrastructure as deployed or production-ready.
  Keep the Terraform draft and workflow prerequisites clearly documented, and
  never put Azure credentials, Terraform state, plans, or real secrets in Git.

## Setup and verification

For local development, use Python 3.11 and run:

```bash
./run.sh
```

For a container build and run, see the README. The primary checks are:

```bash
bash -n run.sh
docker build --tag voice-agent-poc .
docker run --rm --publish 8501:8501 --env-file .env voice-agent-poc
```

With the app running, verify the Streamlit health endpoint:

```bash
curl --fail http://localhost:8501/_stcore/health
```

There is currently no automated test suite in the repository. Do not claim
tests passed unless they were actually run; report clearly when Docker or
external services are unavailable.
