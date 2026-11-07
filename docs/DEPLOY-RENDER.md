# Deploying RideMate on Render

Render's plans and dashboard labels change, so check its current docs for prices, plan limits and
exact menu names. The steps below are the order of work.

## 1. Create the services

1. **PostgreSQL**: create a database in the region closest to your visitors. Note the internal
   hostname, port, database name, user and password from its Connect panel.
2. **Key Value (Redis-compatible)**: create one in the same region. Copy its *internal* URL.
3. **Web Service**: connect the Git repository, choose the **Docker** runtime (the repository's
   `Dockerfile` is used), and set the health check path to `/healthz/`.

## 2. Environment variables (web service)

| Key | Value |
|---|---|
| `SECRET_KEY` | A new random value of 50+ characters |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `yourdomain.example,yourservice.onrender.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://yourdomain.example,https://yourservice.onrender.com` |
| `BEHIND_PROXY` | `True` |
| `SECURE_SSL_REDIRECT` | `True` |
| `SECURE_HSTS_SECONDS` | `3600` at first |
| `ADMIN_URL` | A path of your own, for example `manage-rt-7f3k/` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | From the PostgreSQL service |
| `REDIS_URL` | Internal URL of the Key Value service |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` | Your SMTP provider |
| `SMS_BACKEND` | `twilio` or `http`, with the matching `TWILIO_*` or `SMS_HTTP_*` keys |
| `GOOGLE_MAPS_API_KEY`, `PLAUSIBLE_DOMAIN`, `CONTACT_EMAIL` | Optional |

Never set `SMS_BACKEND=console` or the console email backend on a live service: they write codes
and links to the logs.

## 3. Migrations

Static files are collected while the image builds, so only the database needs a step on each
deploy.

- On a plan with a pre-deploy command, set it to `python manage.py migrate --noinput`.
- Otherwise set the Docker command to
  `sh -c "python manage.py migrate --noinput && gunicorn config.wsgi:application -c gunicorn.conf.py"`.

The first deploy creates the tables (`core/migrations/` must be committed). Then open the
service's Shell and run `python manage.py createsuperuser`. Do not run `seed_demo`.

## 4. HTTPS and the domain

Render issues a certificate for the `onrender.com` address immediately. For your own domain:
add it under the service's custom domain settings, create the DNS record Render shows at your
registrar, wait for verification and the certificate, then add the domain to `ALLOWED_HOSTS` and
`CSRF_TRUSTED_ORIGINS`. Keep `SECURE_HSTS_SECONDS` at 3600 for the first week. When every page
and subdomain you use is HTTPS-only, raise it (for example 86400, then 31536000) and only then
consider `SECURE_HSTS_INCLUDE_SUBDOMAINS` and `SECURE_HSTS_PRELOAD`. Preload is hard to undo.

## 5. After the first deploy

- Open `/healthz/`, `/`, `/signup/`, and a URL that does not exist (the designed 404).
- Sign up with a real phone number and check that the code arrives by SMS and the confirmation
  email arrives.
- Log in to the admin at your `ADMIN_URL`.

## 6. Rollback

- **Code:** in the service's deploys list, redeploy the last good deploy. Do this first when a
  release misbehaves.
- **Database:** write migrations so the previous release still runs against the new schema
  (add columns as optional first, remove them one release later). If a migration must be undone,
  run `python manage.py migrate core <previous migration name>` from the Shell, then redeploy the
  old code.
- **Data:** restore from the database backup only when data was damaged. Test a restore into a
  scratch database before you need it.
