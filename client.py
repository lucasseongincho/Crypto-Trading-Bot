from coinbase.rest import RESTClient 
from auth import API_KEY, API_SECRET

# The Advanced Trade SDK handles both authenticated and public data via one client
# It automatically handles JWT generation using the Key and Secret.
client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)

# To mimic the old structure, you can still reference them:
public_client = client 
auth_client = client