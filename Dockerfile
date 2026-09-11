FROM python:3.11-slim

RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

# Nginx default configuration already serves /var/www/html or custom root index.html
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    location / { \
        root /app; \
        index index.html; \
    } \
}' > /etc/nginx/sites-available/default

EXPOSE 80

ENTRYPOINT ["/app/entrypoint.sh"]
