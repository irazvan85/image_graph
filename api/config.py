from http.server import BaseHTTPRequestHandler
import json


DEMO_CONFIG = {
    "analyzers": {
        "ocr": {"enabled": False, "engine": "tesseract"},
        "captioning": {"enabled": False, "model": "blip-base"},
        "embeddings": {"enabled": False, "model": "clip-ViT-B/32"},
        "object_detection": {"enabled": False, "model": "yolov8n"},
        "face_detection": {"enabled": False}
    },
    "llm": {
        "enabled": False,
        "active": False,
        "provider": "openai",
        "model": "gpt-4-vision-preview",
        "has_api_key": False
    },
    "demo_mode": True
}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(DEMO_CONFIG).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        pass
