import json
with open('models/kokoro/voices.json', 'r') as f:
    data = json.load(f)
    print(list(data.keys()))
