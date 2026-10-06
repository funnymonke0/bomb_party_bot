FROM python:3.14-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium chromium-driver ca-certificates fonts-liberation \
    libnss3 libxss1 libasound2 libgbm1 libgtk-3-0 libu2f-udev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir uv && uv sync --frozen

ENV PYTHONUNBUFFERED=1

CMD ["sh", "-c", "uv run celery -A app.BotWorker:worker_app worker --loglevel=info --pool=prefork & exec uv run python -m gunicorn --workers 1 --threads 8 --bind 0.0.0.0:${PORT:-5000} wsgi:app"]
