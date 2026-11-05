FROM python:3.11-slim@sha256:064f01707f2fc8b06bae86bb43875266c6e41bac7994e77ec5dc623c4a4d0545

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock \
    && useradd --create-home --shell /usr/sbin/nologin appuser

COPY --chown=appuser:appuser app.py .
COPY --chown=appuser:appuser pages ./pages

USER appuser

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
