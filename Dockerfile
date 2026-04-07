FROM python:3.11-alpine
WORKDIR /app
COPY . .
CMD sh -c "python -m http.server ${PORT:-8080}"
