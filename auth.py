import json
from pathlib import Path

# 1. Point to the JSON file
KEY_PATH = Path(__file__).parent / "cdp_api_key.json"

# 2. Extract the keys
with open(KEY_PATH, 'r') as f:
    data = json.load(f)
    API_KEY = data.get("name")
    API_SECRET = data.get("privateKey")