import http.server, os, urllib.parse
class H(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        name = os.path.basename(q['name'][0])
        data = self.rfile.read(int(self.headers['Content-Length']))
        open(os.path.join('sheets', name), 'wb').write(data)
        self.send_response(200); self.end_headers(); self.wfile.write(b'ok')
    def log_message(self, *a): pass
http.server.ThreadingHTTPServer(('127.0.0.1', 8766), H).serve_forever()
