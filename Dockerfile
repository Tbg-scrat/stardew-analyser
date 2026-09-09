# Lightweight Python image for Stardew Valley Save File Watcher
FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SAVES_DIR=/saves \
    OUTPUT_FILE=/app/web/index.html \
    TEMPLATES_DIR=/app/templates \
    DEBOUNCE_SECONDS=2.0

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and templates
COPY parser.py renderer.py watcher.py ./
COPY templates/ ./templates/

# Ensure runtime directories exist
RUN mkdir -p /app/web /saves /app/data

# Run watcher
CMD ["python", "watcher.py"]
