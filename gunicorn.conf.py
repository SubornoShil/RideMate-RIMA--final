
import multiprocessing
import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"  # noqa: S104 (the container is the boundary)

workers = int(os.environ.get("WEB_CONCURRENCY", min(2 * multiprocessing.cpu_count() + 1, 4)))
threads = int(os.environ.get("GUNICORN_THREADS", "2"))
worker_class = "gthread"

timeout = 30
graceful_timeout = 30
keepalive = 5
max_requests = 1000
max_requests_jitter = 100

accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info")
