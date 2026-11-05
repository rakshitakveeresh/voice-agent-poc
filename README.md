# BMW Complaint Chatbot (Streamlit + n8n + Whisper)

This app lets you:

- send text to your n8n webhook
- switch between text mode and voice mode
- record microphone audio in the browser
- transcribe audio with OpenAI Whisper
- send the transcript to the n8n webhook
- play the webhook reply as spoken audio using OpenAI TTS

## Setup

1. Create a Python environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Add your credentials.

You can use either a `.env` file or Streamlit secrets.

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Then fill in:

```env
OPENAI_API_KEY=your_openai_key_here
N8N_WEBHOOK_URL=https://your-n8n-instance.example.com/webhook/customer-care-poc
N8N_USERNAME=
N8N_PASSWORD=
BMW_ID=
LANGUAGE=en
```

Alternatively, create a `.streamlit/secrets.toml` file:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

## Run

```bash
streamlit run app.py
```

## Notes

- Voice input is captured in the browser using `audio-recorder-streamlit`.
- Voice transcription uses the OpenAI Whisper API.
- Voice output uses the OpenAI TTS API.
- The webhook call happens in the app before n8n processes the request.
- If your webhook requires basic auth, set `N8N_USERNAME` and `N8N_PASSWORD`.
- `session_id` is auto-generated in the app if the webhook does not provide one, so it is not strictly required.
