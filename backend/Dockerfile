FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md requirements.lock ./
COPY src ./src

RUN python -m pip install --no-cache-dir --constraint requirements.lock . \
    && useradd --create-home --uid 10001 appuser

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1

CMD ["python", "-m", "uvicorn", "main:app", "--app-dir", "/app/src", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
