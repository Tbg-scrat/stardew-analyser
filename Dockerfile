FROM python:3.11-slim

# Install Nginx
RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application files
COPY . .

# Configure Nginx to serve generated debug.html as index.html
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    location / { \
        root /app; \
        index debug.html; \
    } \
}' > /etc/nginx/sites-available/default

EXPOSE 80

ENTRYPOINT ["/app/entrypoint.sh"]
