FROM python:3.11-slim

RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir jinja2 watchdog

COPY . .

RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    location / { \
        root /app; \
        index index.html; \
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"; \
    } \
}' > /etc/nginx/sites-available/default


EXPOSE 80

ENTRYPOINT ["/app/entrypoint.sh"]
