from flask import Flask
from flask_cors import CORS
import sys
import os

print(f"Test Server Starting... Python: {sys.executable}")
app = Flask(__name__)
CORS(app)

@app.route('/')
def hello():
    return "Hello World - Backend is Alive"

@app.route('/api/health')
def health():
    return {"status": "ok", "local": True}

if __name__ == "__main__":
    print("Binding to 0.0.0.0:5005")
    try:
        app.run(host='0.0.0.0', port=5005, debug=False)
    except Exception as e:
        print(f"CRASH: {e}")
