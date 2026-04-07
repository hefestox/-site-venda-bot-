FROM python:3.11-alpine
WORKDIR /app
COPY . .
CMD python -m http.server $PORT
