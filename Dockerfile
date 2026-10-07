FROM python:3.11-slim

# Install system dependencies (nginx + build tools for xnbcli)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    wget \
    unzip \
    && mkdir -p /app/bin/xnbcli \
    && wget https://github.com/LeonBlade/xnbcli/releases/download/v1.0.7/xnbcli-linux.zip -O /tmp/xnbcli.zip \
    && unzip -q /tmp/xnbcli.zip -d /app/bin/xnbcli \
    && chmod +x /app/bin/xnbcli/xnbcli /app/bin/xnbcli/unpack.sh \
    && rm /tmp/xnbcli.zip \
    && apt-get purge -y wget unzip \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir jinja2 watchdog pillow

COPY . .

# Ensure container startup script is executable
RUN chmod +x /app/entrypoint.sh

# Configure Nginx with root app mapping and /cache/ alias
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    location / { \
        root /app; \
        index index.html; \
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"; \
    } \
    location /cache/ { \
        alias /cache/; \
        add_header Cache-Control "public, max-age=86400"; \
    } \
}' > /etc/nginx/sites-available/default

EXPOSE 80

ENTRYPOINT ["/app/entrypoint.sh"]
