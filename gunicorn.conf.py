"""Gunicorn settings. Everything tunable comes from the environment."""
import multiprocessing
import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"  # noqa: S104 (the container is the boundary)

# Threads share one process's memory, so a small worker count goes a long way.
workers = int(os.environ.get("WEB_CONCURRENCY", min(2 * multiprocessing.cpu_count() + 1, 4)))
threads = int(os.environ.get("GUNICORN_THREADS", "2"))
worker_class = "gthread"

timeout = 30
graceful_timeout = 30
keepalive = 5

# Recycle workers now and then so a slow leak never becomes an outage.
max_requests = 1000
max_requests_jitter = 100

accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info")
