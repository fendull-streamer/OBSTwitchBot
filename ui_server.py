import http.server
import socketserver
import threading

PORT = 8000

Handler = http.server.SimpleHTTPRequestHandler

class MessageHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"hello")
        return

class UIServer(threading.Thread):
    def __init__(self, bot):
        threading.Thread.__init__(self)
        self.httpd = None
        self.bot = bot
    
    def run(self):
        self.httpd = socketserver.TCPServer(("", PORT), MessageHandler)
        print("serving at port", PORT)
        self.httpd.serve_forever()

    def stop(self):
        self.httpd.shutdown()

    