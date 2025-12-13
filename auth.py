# auth.py (CORRECTED CODE)
import os
from coinbase.rest import RESTClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Load API Credentials ---
# Pass the variable NAME (string) to os.getenv(), not the value.
API_KEY = os.getenv("COINBASE_API_KEY") 
API_SECRET = os.getenv("COINBASE_API_SECRET")

if not all([API_KEY, API_SECRET]):
    raise ValueError("Missing COINBASE_API_KEY or COINBASE_API_SECRET in .env file.")

# --- Initialize Coinbase Clients ---

# The RESTClient handles both public (unauthenticated) and private (authenticated) calls.
# It automatically uses the key and secret to generate JWTs for authentication.

# 1. Private Client (for trading, balance check, and order placement)
try:
    # The key should be passed as a raw string.
    # The SDK internally handles the token generation for the Advanced Trade API.
    private_client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
    print("Private client initialized.")
except Exception as e:
    # If the failure is due to MalformedFraming, it means the structure is wrong.
    # Check if the secret is a single string and retry initialization with the key encoded/decoded
    if "MalformedFraming" in str(e):
        print("WARNING: MalformedFraming error detected. Please verify your COINBASE_API_SECRET format.")
        # If the error persists, the key is structurally incompatible with the SDK's Ed25519 expectation.
        # No further code fix can resolve an invalid key structure.
        raise RuntimeError(f"Failed to initialize Private Coinbase Client: Key Format Error: {e}")

    raise RuntimeError(f"Failed to initialize Private Coinbase Client: {e}")

# 2. Public Client (for fetching unauthenticated data like market candles)
# You can use the private_client for this too, but for clarity, we define one specifically.
# Since the RESTClient automatically authenticates, we use it for both.
public_client = private_client
print("Public client initialized.")