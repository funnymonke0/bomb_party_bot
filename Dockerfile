FROM python:3.14-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium chromium-driver ca-certificates fonts-liberation \
    libnss3 libxss1 libasound2 libgbm1 libgtk-3-0 libu2f-udev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromium-driver

COPY . .

RUN pip install --no-cache-dir uv && uv sync --frozen

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

