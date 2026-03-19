from http.server import BaseHTTPRequestHandler
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from _demo_data import DEMO_GRAPH


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        fmt = "json"
        if "?" in self.path:
            query = self.path.split("?", 1)[1]
            for param in query.split("&"):
                if param.startswith("format="):
                    fmt = param.split("=", 1)[1]

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        if fmt == "graphml":
            self.wfile.write(json.dumps({"graphml": "<graphml/>"}).encode())
        elif fmt == "cypher":
            self.wfile.write(json.dumps({"cypher": "// Demo export"}).encode())
        else:
            self.wfile.write(json.dumps(DEMO_GRAPH).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        pass

