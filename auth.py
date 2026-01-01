import json
import os
from pathlib import Path
from coinbase.rest import RESTClient

# 1. Point to the JSON file
KEY_PATH = Path(__file__).parent / "cdp_api_key.json"

# 2. Extract the keys
if not KEY_PATH.exists():
    print(f"❌ Error: {KEY_PATH} not found!")
    exit()

with open(KEY_PATH, 'r') as f:
    data = json.load(f)
    # Using .get() prevents crashing if keys are missing
    API_KEY = data.get("name")
    API_SECRET = data.get("privateKey")

# 3. Initialize the actual Client object
# This is what 'from auth import client' looks for!
client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)

print("Coinbase Client Initialized Successfully")