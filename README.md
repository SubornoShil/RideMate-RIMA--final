# RideMate

Community carpooling across Bangladesh. People post a route they already travel, others ask for a seat,
and the fare is split. Trust is the product: Verified Circles, women-only rides, Guardian Mode
and a weighted Trust Score.

Django 5.2 LTS (`Django==5.2.7`), Python 3.10+, three apps (`accounts`, `rides`, `trust`; see OWNERSHIP.md), server-rendered templates,
hand-written CSS, plain ES modules. SQLite by default, PostgreSQL when `DB_NAME` is set.
Every page works without JavaScript; the scripts only add polish.

> **Status:** nothing in this repository has been run end to end on a machine with Django
> installed. Follow "First run" below and fix whatever the first `check` or `test` reports.

## First run

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python manage.py makemigrations accounts rides trust
python manage.py migrate
python manage.py check
python manage.py test
python manage.py seed_demo
python manage.py runserver
```

If PowerShell blocks the activate script, run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once and try again.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py makemigrations accounts rides trust
python manage.py migrate
python manage.py check
python manage.py test
python manage.py seed_demo
python manage.py runserver
```

`makemigrations accounts rides trust` is the one step that cannot be skipped: no migration files
are committed yet. Commit what it creates (`accounts/migrations/0001_initial.py`, and the same in
`rides` and `trust`).

Open <http://127.0.0.1:8000/>. In development the phone code and the email links are printed in
the terminal that runs `runserver`.

## Tests

```bash
python manage.py test            # everything
python manage.py test tests.test_rides   # one module
ruff check .                     # lint
```

## Admin account

```bash
python manage.py createsuperuser
```

Staff accounts get a profile automatically the first time one is needed. The admin lives at
`/admin/` in development and at the path in `ADMIN_URL` in production. Staff can also open
`/analytics/`.

## Demo logins

`python manage.py seed_demo` creates five members (Suborno Shil, Tanvir Ahmed, Sadia Rahman, Famin Khan, Rafa Amon), all with password `demo12345`:

| Username | Gender |
|---|---|
| suborno | M |
| tanvir | M |
| sadia | F |
| famin | M |
| rafa | M |

It also creates the circles `MIRPUR24` and `DHAKAUNI`, four upcoming rides (one women-only) and
three guardians.

> **Never create demo accounts on a live server.** They share a public password. The command
> refuses to run when `DEBUG` is off unless you pass `--allow-production`; do not pass it.

## Configuration

Everything comes from environment variables; `.env.example` lists them all. Development needs
none of them. In production the app refuses to start without `SECRET_KEY` and `ALLOWED_HOSTS`.

| Variable | Purpose |
|---|---|
| `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` | Required in production |
| `DEBUG` | Off by default in production settings |
| `BEHIND_PROXY` | `True` when a proxy terminates HTTPS (Render, most hosts) |
| `SECURE_SSL_REDIRECT`, `SECURE_HSTS_*` | HTTPS redirect and HSTS; raise HSTS in stages |
| `ADMIN_URL` | Admin path in production, for example `manage-rt-7f3k/` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL when `DB_NAME` is set |
| `REDIS_URL` | Shared cache for login lockout across workers |
| `EMAIL_*`, `DEFAULT_FROM_EMAIL` | SMTP for confirmation and reset emails |
| `SMS_BACKEND` | `console` (development), `twilio` or `http` |
| `TWILIO_*`, `SMS_HTTP_*` | Credentials for the chosen SMS backend |
| `GOOGLE_MAPS_API_KEY` | Optional Places Autocomplete on the ride form |
| `PLAUSIBLE_DOMAIN` | Optional privacy-friendly analytics, off when empty |
| `CONTACT_EMAIL` | Shown in the footer when set |

`SENTRY_DSN` is listed in `.env.example` but not wired. To use Sentry, add `sentry-sdk` to
`requirements.txt` and a guarded `sentry_sdk.init(...)` in `config/settings/production.py`.

The console SMS and email backends print codes and links. They are for development only; never
point a live site at them.

## Where to edit things

| What | Where |
|---|---|
| Page copy | `templates/*.html` (shared) and each app's own `templates/` folder |
| Terms and Privacy (drafts, need legal review) | `templates/terms.html`, `templates/privacy.html` |
| Place suggestions (all divisions) | `rides/areas.py` |
| Demo data | `rides/management/commands/seed_demo.py` |
| Colours, type scale, spacing | the `:root` tokens at the top of `static/css/main.css` |
| Fonts | `static/css/fonts.css`, files in `static/fonts/` |
| Business rules | `accounts/services.py` (login, codes), `rides/services.py` (seats, requests), `trust/services.py` (ratings, guardians, circles) |
| Open Graph card and icons | `static/img/`, `static/site.webmanifest` |

## Front end

The design rule is that every element hangs from a thread. Scripts live in `static/js/` as small
ES modules behind one entry point, `main.js`. They are read through `data-*` attributes in the
templates, so removing a module removes only its effect.

- `lanes.js` moves vehicle markers along SVG paths. The hero map (`partials/routemap.html`) has a
  car, a bike and a CNG travelling between Bangladeshi cities; a car follows your scroll through
  "How a ride gets tied together"; a CNG loops in the closing block. Add a `.vehicle` group with
  `data-track` (a path id), `data-speed`, `data-offset`, `data-scale`, `data-anchor="center"`.
  Loops pause offscreen and in hidden tabs; with reduced motion the markers stand still.
- Marker glyphs are in `partials/marker.html` (`kind`: car, cng, bike, rickshaw). The Bangladesh
  outline and city positions are hand-placed approximations, not survey data.
- The four "How it works" mock screens are static HTML with example data, marked `aria-hidden`.
- There is no custom cursor. The pointer stays the normal system pointer.
- Google Places Autocomplete loads only when `GOOGLE_MAPS_API_KEY` is set, and falls back to the
  plain input and the `<datalist>` of places (all eight divisions) on any failure.
- Sound effects are off until the visitor switches them on in the footer. Nothing autoplays.
- The fare meter in the footer reveals a split link if you hold its heading for about a second
  (hold Enter or Space on the keyboard).
- Fonts: Playfair Display (headings, Latin) with Noto Serif Bengali for Bangla headings, and
  Hind Siliguri for text (Latin and Bangla), loaded from Google Fonts with `font-display: swap`.
  To self-host, see the note at the top of `fonts.css` and drop the two Google hosts from
  `config/middleware.py`.
- The JS modules import each other by relative path. Django's manifest storage only hashes
  `main.js`; the other modules are served by WhiteNoise under their plain names with a short
  cache lifetime, so a deploy never leaves visitors on stale modules.

Content-Security-Policy is built per request in `config/middleware.py` with a nonce. Inline scripts
need `nonce="{{ csp_nonce }}"`. With a Maps key the policy also allows `maps.googleapis.com` and
inline style attributes, because Maps writes them.

## Docker

```bash
docker build -t ridetogether .
docker run --rm -p 8000:8000 \
  -e SECRET_KEY=change-me-to-a-long-random-string \
  -e ALLOWED_HOSTS=localhost \
  -e SECURE_SSL_REDIRECT=False \
  ridetogether
```

The image runs as a non-root user, collects static files at build time and checks `/healthz/`.
Run `python manage.py migrate --noinput` against your database before the first start (see the
deployment guide). The default SQLite file is not suitable inside a container; set the `DB_*`
variables.

## Deploying

`docs/DEPLOY-RENDER.md` covers Render: environment variables, migrations, static files, HTTPS,
custom domain and rollback.

## Before going live

- [ ] `SECRET_KEY` is a new long random value, `DEBUG` is off, `ALLOWED_HOSTS` and
      `CSRF_TRUSTED_ORIGINS` list only your domain
- [ ] `python manage.py check --deploy` reports nothing (CI runs it)
- [ ] PostgreSQL configured through the `DB_*` variables, backups switched on and a restore tested
- [ ] SMS gateway set (`SMS_BACKEND=twilio` or `http`) and a real phone code received
- [ ] SMTP email set and a real confirmation and reset email received
- [ ] `REDIS_URL` set so login lockout is shared between workers
- [ ] `collectstatic` runs in the build (the Dockerfile does it)
- [ ] `ADMIN_URL` changed from the default and the admin account uses a strong password
- [ ] No demo accounts exist; `seed_demo` was never run on this database
- [ ] Terms and Privacy reviewed by someone qualified; the footer claim that the platform takes
      no cut is true
- [ ] Custom 400, 403, 404 and 500 pages checked on the live host
- [ ] Security headers and SSL grade checked; HSTS raised in stages from the 1 hour default
- [ ] Lighthouse on mobile: Performance 90+, LCP under 2.5 s, CLS under 0.1, INP under 200 ms
- [ ] Tried on a real iPhone (Safari) and a real Android phone (Chrome), keyboard-only, and one
      screen reader
- [ ] Uptime monitoring on `/healthz/`
- [ ] If Plausible is on, the privacy page mentions it

## Known gaps

- Login lockout is keyed on `REMOTE_ADDR`. Behind a proxy that is the proxy's address unless the
  platform forwards the client address properly, and a per-process cache loosens the limit across
  several workers. Set `REDIS_URL`.
- Password reset and the resend-email endpoint have no rate limit yet (OTP resend has a 60 second
  wait).
- The fallback font metrics in `fonts.css` are starting values, not measured.
- Bangla names fall back to Noto Sans/Serif Bengali stacks; test real Bangla strings.
- The Places Autocomplete code follows Google's current web-component API but has not been
  tried against a live key.

## Git

Conventional Commit messages (`feat: ...`, `fix: ...`, `docs: ...`, `test: ...`, `chore: ...`).
Install the hooks once with `pre-commit install`. Never commit `.env`, `db.sqlite3` or
`staticfiles/`; `.gitignore` already excludes them.


If you seeded an older copy, run `python manage.py seed_demo --replace-old` to remove the earlier demo accounts (nusrat, rafi, mehedi).

## Regenerating the maps and road scene

`python tools/build_maps.py` rebuilds the hero map (Dhaka city and Bangladesh) and `static/css/mapdata.css` from real latitude/longitude. Drop an official outline at `tools/bangladesh.geojson` first if you want it used. `python tools/build_roadscene.py` rebuilds the animated street scene.
