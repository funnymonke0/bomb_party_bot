FROM python:3.14-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium chromium-driver ca-certificates fonts-liberation \
    libnss3 libxss1 libasound2 libgbm1 libgtk-3-0 libu2f-udev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir uv && uv sync --frozen

ENV PYTHONUNBUFFERED=1
CMD ["gunicorn","--workers","1","--threads","8","--bind","0.0.0.0:$PORT","wsgi:app"]