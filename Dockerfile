FROM caddy:alpine
WORKDIR /app
COPY . .
CMD caddy file-server --root /app --listen :$PORT
