import os

print(os.environ.get("MYSECRET", "Not Found")[:5], "...")
