import base64
import io
import os
import uuid

import requests
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)

st.set_page_config(page_title="BMW Complaint Agent", page_icon="🚗", layout="wide")


def read_dotenv_file():
    values = {}
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(dotenv_path):
        return values

    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"\'')
    return values


def get_env_value(name: str, default: str = "") -> str:
    value = (os.getenv(name) or "").strip()
    if value:
        lowered = value.lower()
        if "your_" in lowered or "example" in lowered or "placeholder" in lowered:
            return default
        return value

    if hasattr(st, "secrets"):
        value = str(st.secrets.get(name, default)).strip()
        if value:
            lowered = value.lower()
            if "your_" in lowered or "example" in lowered or "placeholder" in lowered:
                return default
            return value

    return default


def get_api_key():
    direct = read_dotenv_file().get("OPENAI_API_KEY", "")
    if direct:
        return direct
    return get_env_value("OPENAI_API_KEY", "")


def get_client():
    api_key = get_api_key()
    if not api_key:
        st.error("Missing OpenAI API key. Add it in the sidebar or set OPENAI_API_KEY.")
        st.stop()
    return OpenAI(api_key=api_key)


def get_webhook_config():
    url = get_env_value("N8N_WEBHOOK_URL", "")
    username = get_env_value("N8N_USERNAME", "")
    password = get_env_value("N8N_PASSWORD", "")
    return url, username, password


def extract_response_text(value):
    if isinstance(value, str):
        text = value.strip()
        return text if text else ""
    if isinstance(value, dict):
        for key in ("output", "reply", "response", "message", "answer", "text", "body"):
            if key in value:
                text = extract_response_text(value[key])
                if text:
                    return text
        for nested in value.values():
            text = extract_response_text(nested)
            if text:
                return text
    elif isinstance(value, list):
        for item in value:
            text = extract_response_text(item)
            if text:
                return text
    return ""


def send_to_n8n(message_text: str):
    url, username, password = get_webhook_config()
    if not url:
        raise ValueError("Missing N8N_WEBHOOK_URL. Set it in secrets or the sidebar.")

    session_id = st.session_state.get("session_id") or str(uuid.uuid4())
    st.session_state.session_id = session_id

    payload = {
        "text": message_text,
        "language": st.session_state.get("language", "en"),
        "session_id": session_id,
        "bmw_id": st.session_state.get("bmw_id", ""),
    }

    auth = None
    if username and password:
        auth = (username, password)

    response = requests.post(url, json=payload, auth=auth, timeout=60)
    response.raise_for_status()

    raw_text = response.text.strip()
    if not raw_text:
        raise ValueError(
            "The n8n webhook returned an empty response body (HTTP 200). "
            "Check the workflow and add a 'Respond to Webhook' node returning JSON like {'output': '...'}"
        )

    try:
        data = response.json()
    except ValueError:
        return raw_text

    extracted = extract_response_text(data)
    if extracted:
        return extracted

    if isinstance(data, (dict, list)):
        return json_stringify(data)

    return raw_text


def json_stringify(value):
    if isinstance(value, (dict, list)):
        return str(value)
    return str(value)


def transcribe_audio(audio_value):
    if not audio_value:
        return ""

    if hasattr(audio_value, "read"):
        audio_bytes = audio_value.read()
    elif isinstance(audio_value, (bytes, bytearray)):
        audio_bytes = bytes(audio_value)
    else:
        return ""

    client = get_client()
    stt_model = get_env_value("OPENAI_STT_MODEL", "gpt-4o-mini-transcribe")
    try:
        result = client.audio.transcriptions.create(
            model=stt_model,
            file=("voice.wav", audio_bytes),
            response_format="json",
        )
        text = getattr(result, "text", "")
        return text.strip()
    except Exception as exc:
        st.error(f"Whisper transcription failed: {exc}")
        return ""


def speak_text(text):
    if not text:
        return None
    client = get_client()
    try:
        tts_model = get_env_value("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
        audio_response = client.audio.speech.create(
            model=tts_model,
            voice="alloy",
            input=text,
        )
        audio_bytes = audio_response.read() if hasattr(audio_response, "read") else audio_response.content
        if audio_bytes:
            st.session_state["last_speech_bytes"] = audio_bytes
            return audio_bytes
    except Exception as exc:
        st.warning(f"Text-to-speech failed: {exc}")
    return None


def play_hidden_audio(audio_bytes, mime_type="audio/mpeg"):
    if not audio_bytes:
        return
    encoded = base64.b64encode(audio_bytes).decode("utf-8")
    audio_html = f"""
    <audio autoplay="autoplay" style="display:none;" preload="auto">
        <source src="data:{mime_type};base64,{encoded}" type="{mime_type}">
    </audio>
    """
    components.html(audio_html, height=0, scrolling=False)


def render_message(role, content):
    with st.chat_message(role):
        st.markdown(content)


def handle_user_message(user_text: str, speak_reply: bool = False):
    user_text = user_text.strip()
    if not user_text:
        return

    st.session_state.messages.append({"role": "user", "content": user_text})
    render_message("user", user_text)

    try:
        bot_reply = send_to_n8n(user_text)
    except Exception as exc:
        bot_reply = f"Webhook error: {exc}"

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    render_message("assistant", bot_reply)

    if speak_reply:
        audio_bytes = speak_text(bot_reply)
        if audio_bytes:
            play_hidden_audio(audio_bytes)


if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! I’m your BMW support assistant. I can help with charging, delivery, connected services, or warranty questions.",
        }
    ]

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "current_view" not in st.session_state:
    st.session_state.current_view = "chat"

from pages.human_overview import render_human_overview

st.title("Support Assistant")

with st.sidebar:
    st.header("Settings")
    mode = st.radio("Mode", ["Normal mode", "Voice mode"], horizontal=True)
    st.text_input("BMW ID", key="bmw_id", placeholder="optional")
    st.text_input("Language", key="language", value="en")
    if st.button("Human Overview"):
        st.session_state.current_view = "human_overview"
        st.rerun()
    if st.session_state.current_view == "human_overview" and st.button("Back to chat"):
        st.session_state.current_view = "chat"
        st.rerun()
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! I’m your BMW support assistant. I can help with charging, delivery, connected services, or warranty questions.",
            }
        ]
        st.rerun()
    st.caption("Credentials are read from .env or Streamlit secrets.")

if st.session_state.current_view == "human_overview":
    render_human_overview()
else:
    for message in st.session_state.messages:
        render_message(message["role"], message["content"])

    prompt = st.chat_input("Say or record something", accept_audio=True)

    if prompt:
        if prompt.text:
            handle_user_message(prompt.text, speak_reply=(mode == "Voice mode"))

        if getattr(prompt, "audio", None) is not None:
            audio_file = prompt.audio
            with st.spinner("Transcribing your audio..."):
                transcript = transcribe_audio(audio_file)

            if transcript:
                handle_user_message(transcript, speak_reply=(mode == "Voice mode"))
            else:
                st.warning("No speech could be transcribed. Please try again.")

