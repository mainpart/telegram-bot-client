from http.server import BaseHTTPRequestHandler, HTTPServer
import os


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/healthz", "/readyz"):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        # suppress default logging
        return


def main():
    port = int(os.environ.get("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()


