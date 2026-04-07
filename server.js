const handler = require('serve-handler');
const http = require('http');

const port = process.env.PORT || 3000;
const host = '0.0.0.0';

const server = http.createServer((request, response) => {
  return handler(request, response, {
    public: '.'
  });
});

server.listen(port, host, () => {
  console.log(`Server running at http://${host}:${port}`);
});
