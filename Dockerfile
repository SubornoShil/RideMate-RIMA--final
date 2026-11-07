# syntax=docker/dockerfile:1

FROM python:3.12-slim AS build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
# The throwaway values exist only so settings import; nothing from this step is kept in the image env.
RUN DJANGO_SETTINGS_MODULE=config.settings.production \
    SECRET_KEY=build-step-only ALLOWED_HOSTS=localhost \
    python manage.py collectstatic --noinput

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8000
RUN useradd --system --create-home --uid 10001 app
WORKDIR /app
COPY --from=build /opt/venv /opt/venv
COPY --from=build --chown=app:app /app /app
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python", "docker/healthcheck.py"]
CMD ["gunicorn", "config.wsgi:application", "-c", "gunicorn.conf.py"]
