
import os
import sys
import urllib.request

port = os.environ.get("PORT", "8000")
hosts = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()]
host = hosts[0].lstrip(".") if hosts else "localhost"
request = urllib.request.Request(f"http://127.0.0.1:{port}/healthz/", headers={"Host": host})
try:
    with urllib.request.urlopen(request, timeout=4) as response:  # noqa: S310
        sys.exit(0 if response.status == 200 else 1)
except OSError:
    sys.exit(1)
