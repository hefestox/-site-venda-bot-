FROM node:18-alpine
WORKDIR /app
COPY . .
RUN npm install -g serve
CMD serve . -l $PORT --single
