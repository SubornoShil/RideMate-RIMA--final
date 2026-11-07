> **Update:** the single `core` app described below was split into three apps: `accounts`, `rides` and
> `trust`. See OWNERSHIP.md for what lives where. File paths below that start with `core/` are historical.

# RideMate: status after Parts 5 and 6

Parts 5 and 6 are now written (JavaScript modules in `static/js/`, WebGL hero in `static/js/thread.js`,
icons, Open Graph image and manifest in `static/img/` and `static/site.webmanifest`, `README.md`, `Dockerfile`,
`.dockerignore`, `gunicorn.conf.py`, `docker/healthcheck.py`, `docs/DEPLOY-RENDER.md`, `.github/workflows/ci.yml`,
`.pre-commit-config.yaml`). Small edits to earlier files: `base.html` (inline `js` class script with a 4 s safety
net), `main.css` (WebGL keeps the SVG labels; tabular numbers; `.places`), `production.py` (silences only
`security.W005` and `security.W021`). Still never run against Django: do section 7 first.

---

**Palette and hero change (latest):** charcoal #171717, forest #06110C, crimson #A31C1B (plus sage and cream for text and chips); Bangladesh route-map hero with vehicle markers; four-step "How it works" with mock screens; Playfair Display + Hind Siliguri. Cartoon vehicle art and the scene were removed.

**Earlier redesign:** rebranded to RideMate using the supplied logo colours; colourful theme layer at the end of
`main.css`; WebGL hero, `thread.js`, `hero.js` and the cursor ring were removed; `lanes.js` animates a CNG and a
rickshaw along SVG road threads (time loop, or scroll-linked); fonts are Baloo Da 2 + Hind Siliguri from Google Fonts
(CSP updated); places list covers all divisions (`core.areas.AREAS`); copy says Bangladesh, not Dhaka. The older text
below still describes the first design and names the WebGL hook table, which no longer applies.

---

# RideMate: handoff brief

Paste this whole file into the next AI, together with the project zip (`ridetogether-parts-1-4.zip`).
Parts 1 to 4 are written. Parts 5 and 6 are not. **Nothing has been run**: Django was not installed
where this was written and there was no network. Everything was only syntax-checked (`compileall`,
template tag balance, URL-name and include audits, a CSS class-coverage check).

## 1. What the project is

RideMate: community carpooling web app for Dhaka, Bangladesh. People post a route they already
travel, others request a seat, they split the fare. Trust and safety are the point: Verified Circles,
women-only rides, Guardian Mode (SMS to up to 3 guardians when a seat is confirmed), weighted Trust Score.

Two source prompts were merged:
- **Functional spec**: Django 5.x, one app `core`, server-rendered, every page works without JavaScript,
  SQLite by default and PostgreSQL when `DB_NAME` is set, env-driven settings.
- **Creative-director/engineering prompt**: award-level design, strict standards (semantic HTML, CSS `@layer`,
  ES modules, CSP with nonces, WCAG 2.2 AA, Lighthouse mobile 90+, tests, Docker, CI, deploy guide).

### Approved design concept: "The Thread"
A ride is one line two strangers share; trust is how that line is drawn. One rule the design never breaks:
nothing sits off the thread (every element hangs from a line).
- Palette: Bone `#F3EEE3`, Tar `#16130F`, CNG Green `#0E6B4B`, Lal Signal `#E4381F`
  (large text/UI only, 3.7:1; text uses darker `#C42A12`, 4.9:1), Kalojam Plum `#4A1F3D` (women-only),
  Turmeric `#E8A317` (unexpected accent). Measured: Tar/Bone 16:1, Green/Bone 5.6:1, Plum/Bone 11.7:1,
  Turmeric/Tar 8.5:1.
- Type: Bricolage Grotesque (display) + Source Serif 4 (text), Noto Sans/Serif Bengali fallbacks.
- Motion: one easing `cubic-bezier(.2,.8,.2,1)`; 160ms feedback, 420ms reveals, 900ms draws; only
  `transform`, `opacity`, `clip-path`, `stroke-dashoffset` animate.
- **Gasp moment**: hero thread draws itself Mirpur to Motijheel in 1.2s; a second thread bends toward the
  pointer and within 80px the two knot into one labelled "one fare, two people". Tap does the same on touch.
  Without JS it is a static SVG.
- **Rabbit hole**: hold the footer fare meter (about 1.2s) to open a split-fare layer with a shareable link
  per split.
- Refusing: map-pin hero or stock car photo; fake testimonials or gamified trust leaderboard; hiding safety
  rules behind motion.

### Assumptions made (user approved without answering)
English only; Render as the deployment host; no Tailwind CDN (hand-written CSS, strict CSP);
Django 5.2 LTS (`Django==5.2.7`).

## 2. Deviations from the specs (deliberate)
- App is top-level `core/` (spec path `core/management/commands/seed_demo.py`), not `apps/core/`.
- Women-only rides return **404** (not 403) to non-women and anonymous users, so existence is not leaked.
- Default Django `User` + `UserProfile` one-to-one (per functional spec), not a custom user model.
- Own small CSP middleware with per-request nonce instead of `django-csp`.
- Settings split into `config/settings/{base,development,production}.py`; dev and prod copy upper-case names
  from base via `_load.load_base(globals())` (no wildcard imports).
- Default error views (`django.views.defaults.*`) are used for 400/403/404/500 with designed templates.
- Staff accounts from `createsuperuser` get a `UserProfile` lazily via `services.get_profile()`
  (phone placeholder `staff<id>`).
- `RidePost.available_seats` is both the posted total and the live remaining count (decremented on accept).

## 3. File tree (as of Part 4)
```
.env.example
.gitignore
config/__init__.py
config/asgi.py
config/env.py
config/settings/__init__.py
config/settings/_load.py
config/settings/base.py
config/settings/development.py
config/settings/production.py
config/urls.py
config/wsgi.py
core/__init__.py
core/admin.py
core/apps.py
core/areas.py
core/backends.py
core/context_processors.py
core/decorators.py
core/forms.py
core/management/__init__.py
core/management/commands/__init__.py
core/management/commands/seed_demo.py
core/middleware.py
core/migrations/__init__.py
core/models.py
core/phone.py
core/services.py
core/sms.py
core/urls.py
core/views.py
manage.py
pyproject.toml
requirements-dev.txt
requirements.txt
static/css/fonts.css
static/css/main.css
templates/400.html
templates/403.html
templates/404.html
templates/500.html
templates/analytics.html
templates/base.html
templates/circles.html
templates/dashboard.html
templates/email/verify_email.txt
templates/errors/_thread.html
templates/errors/standalone_base.html
templates/home.html
templates/login.html
templates/notifications.html
templates/partials/field.html
templates/partials/form_errors.html
templates/partials/ride_stop.html
templates/partials/vehicle_glyph.html
templates/privacy.html
templates/profile.html
templates/registration/password_reset_complete.html
templates/registration/password_reset_confirm.html
templates/registration/password_reset_done.html
templates/registration/password_reset_email.txt
templates/registration/password_reset_form.html
templates/registration/password_reset_subject.txt
templates/review_form.html
templates/ride_detail.html
templates/ride_form.html
templates/robots.txt
templates/signup.html
templates/terms.html
templates/verify_phone.html
tests/__init__.py
tests/factories.py
tests/test_misc.py
tests/test_otp.py
tests/test_reviews_guardians.py
tests/test_rides.py
tests/test_signup_login.py
```

## 4. Core code conventions (names to keep consistent)

URL namespace `core`. Names: `home, healthz, signup, login, logout, verify_phone, resend_otp, resend_email,
verify_email(token), ride_new, ride_detail(pk), ride_request(pk), ride_complete(pk), ride_cancel(pk),
review_new(pk, profile_id), request_accept(pk), request_reject(pk), request_cancel(pk), dashboard, profile,
guardian_add, guardian_delete(pk), circles, circle_join, circle_leave(pk), notifications, analytics, terms,
privacy, robots, sitemap`. Un-namespaced (in `config/urls.py`): `password_reset, password_reset_done,
password_reset_confirm, password_reset_complete`. Admin path comes from env `ADMIN_URL` (default `admin/`).

Models (all domain FKs point at `UserProfile`): `UserProfile, Circle, GuardianContact, RidePost, RideRequest,
Review, Notification, ModerationLog` (moderator FK is the Django user). `TextChoices` everywhere.
Constraints: unique `(ride, requester)`; unique `(ride, rater, rated_user)`; review score 1 to 5; no self-review.

`core/services.py` holds every business rule (views stay thin). Key API:
`get_profile, notify, search_rides(viewer, start, end, vehicle, women_only), site_counts, can_view_ride,
can_see_women_only, ride_participants, ride_contacts, send_request, decide_request(request_id, host, accept),
cancel_request, complete_ride, cancel_ride, moderator_cancel_ride, review_problem, submit_review, add_guardian,
join_circle, issue_otp(session, profile), check_otp(session, profile, code) -> OtpResult, otp_resend_wait,
otp_attempts_left, is_login_locked / register_login_failure / clear_login_failures, make_email_token,
confirm_email_token, send_confirmation_email, send_guardian_alerts`. `RideError` = user-safe business error.
Accepting uses `transaction.atomic` + `select_for_update` (no-op on SQLite); guardian SMS runs via
`transaction.on_commit`.

Session keys for the OTP: `otp_hash, otp_expires, otp_attempts, otp_sent_at` (only an HMAC hash is stored).
Login uses a two-step view; `login_identifier` is kept in the session; lockout is per identifier + `REMOTE_ADDR`
in the cache (5 failures, 15 minutes). Cache is Redis when `REDIS_URL` is set, else per-process LocMem.

SMS (`core/sms.py`): `send_sms(to, message) -> bool`, never raises. Backends via `SMS_BACKEND`:
`console` (default, logs the message including OTP; dev only), `twilio`, `http` (JSON POST with bearer token).

Templates: `templates/` (base, home, signup, login, verify_phone, ride_form, ride_detail, review_form, dashboard,
profile, circles, notifications, analytics, terms, privacy, 400/403/404/500, `errors/`, `partials/`,
`registration/`, `email/`, `robots.txt`). Context processor `core.context_processors.site` provides
`csp_nonce, GOOGLE_MAPS_API_KEY, PLAUSIBLE_DOMAIN, CONTACT_EMAIL, unread_count, nav_profile, email_unconfirmed`.

Env vars: see `.env.example` (`SECRET_KEY, DEBUG, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, BEHIND_PROXY,
SECURE_SSL_REDIRECT, SECURE_HSTS_*, ADMIN_URL, DB_*, REDIS_URL, EMAIL_*, SMS_*, TWILIO_*, GOOGLE_MAPS_API_KEY,
PLAUSIBLE_DOMAIN, CONTACT_EMAIL, SENTRY_DSN`). `manage.py` defaults to development settings; `wsgi/asgi` default
to production (which refuses to start without `SECRET_KEY` and `ALLOWED_HOSTS`).

Seed: `python manage.py seed_demo` creates suborno (M), tanvir (M), sadia (F), famin (M), rafa (M),
password `demo12345`, circles `MIRPUR24` and `DHAKAUNI`, four future rides (one women-only), three guardians.
It refuses to run with `DEBUG` off unless `--allow-production`. README must warn never to seed a live server.

Tests (`tests/`, run with `python manage.py test`): sign-up form and view, phone formats, login backend,
lockout, OTP (correct, wrong, lock after 5, expired, resend wait), women-only visibility and direct-URL 404,
circle priority, request flow (no oversell, seat return, permissions, re-send, DB constraints, contacts),
reviews (0.5 weight for accounts under 7 days, trust maths 86.7 example, labels), guardians (limit 3, alerts),
404 page, healthz, staff-only analytics. Tests that render pages need the templates (now present) and static
files (see section 6).

## 5. CSS contract (done: `static/css/main.css`, `static/css/fonts.css`)
`@layer reset, base, layout, components, motion, utilities`; tokens on `:root`; light and dark; reduced-motion
finishes states instead of switching the page off. The CSS expects JavaScript to add:
- `html.js` as early as possible. **Recommended**: a tiny nonce'd inline script in `<head>` of `base.html`:
  `<script nonce="{{ csp_nonce }}">document.documentElement.classList.add('js')</script>` to avoid a flash.
- `html.webgl` when the WebGL hero is running (CSS then shows the canvas and fades the SVG).
- `.is-in` on `[data-reveal]` elements when they enter the viewport.
- `.is-met` on `li[data-rule]` in the password checklist.
- `.cursor` element (+ `.is-on`, `.is-link`, `.is-text`) and `.intro` overlay (+ `.is-leaving`, `[hidden]`)
  created by JS only.
Fonts: `fonts.css` currently uses `local()` sources only. To self-host, put subset woff2 files in
`static/fonts/`, add `url(...)` sources and preload tags. Never reference a missing file (collectstatic fails
on it with the manifest storage).

## 6. WHAT IS LEFT

### Part 5: JavaScript, shaders, assets
Create `static/js/main.js` (single ES-module entry, small modules, no jQuery, no `var`, no inline handlers,
no `console.log`, `AbortController` cleanup, passive listeners, rAF not `setTimeout`, feature-detect everything).
Budget: initial JS under 150KB gzipped, WebGL initialised after first paint via dynamic `import()`.
Behaviour the templates already depend on (hooks are `data-*` attributes):

| Hook | Where | Behaviour |
|---|---|---|
| `[data-reveal="slide\|clip\|scale\|draw"]` | home, footer, ride page | IntersectionObserver adds `.is-in`; no IO means add to all |
| `[data-thread-hero]`, `canvas[data-thread-canvas]` | home hero | WebGL (raw, OGL or Three.js, self-hosted and version-pinned) fragment-shader thread; second thread follows pointer; within 80px both knot; tap on touch; add `html.webgl`; skip on `prefers-reduced-motion`, coarse/low-power; dispose resources; pause offscreen and on `visibilitychange` |
| `[data-magnetic]` | primary buttons | magnetic pull, fine pointer + hover only |
| `.cursor` | whole site | trailing ring, fine pointer only, contextual states for links and text |
| `[data-count]` | tally, trust score | count-up; respect reduced motion; values may be like `100.0` |
| `[data-toggle-password]` (inside `[data-password-group]` or the form) | signup, login | unhide the button, toggle `type`, set `aria-pressed` and label |
| `[data-strength]` with `meter` and `li[data-rule="number\|case\|symbol\|length"]` | signup | unhide; listen to `#id_password1`; mark `.is-met`; meter 0 to 4; `length` rule is 12+ chars; these are "stronger, not required" |
| `[data-countdown="N"]` on the resend button | verify page | live countdown in the label; do not break the server-side 60s throttle |
| `details#fare-meter[data-meter]` | footer | show `[data-meter-live]`, hide `[data-meter-static]`; `#meter-fare`, `#meter-seats`, `#meter-out` ("Tk N each"); hold `summary` about 1.2s to reveal `[data-meter-secret]` with a shareable link; read `#split=fare:seats` on load to prefill and open |
| `[data-sound-toggle]` | footer | unhide; tiny WebAudio tick effects; **muted by default**, never autoplay; `aria-pressed`; remember choice in guarded `localStorage` |
| `form[data-ride-form][data-maps-key]` | ride form | only if key non-empty: load Google Maps JS lazily, new Places Autocomplete restricted to Bangladesh (`bd`), fill hidden `#id_start_latitude/_longitude/#id_end_latitude/_longitude`; otherwise leave the plain input + `<datalist id="dhaka-areas">` |
| `.toast` | flash messages | auto-hide non-error toasts after about 6s via `hidden` |
| `.intro` | first visit per session | skippable overlay under 1.5s, never blocks content |
| tab title | all pages | change `document.title` when the tab is hidden, restore on return (optional favicon swap) |
| View Transitions | navigation | CSS already opts in; optional JS only for fallbacks |

Everything must be optional enhancement: content, forms and navigation work with JS off, keyboard, find-in-page
and back button never hijacked.

Assets to create (all referenced by `base.html`; missing ones cause 404s, and under
`CompressedManifestStaticFilesStorage` a missing file referenced by `{% static %}` breaks `collectstatic`):
`static/js/main.js`, `static/img/favicon.svg`, `static/img/apple-touch-icon.png` (180x180),
`static/img/og.png` (designed 1200x630), `static/site.webmanifest` (name, short_name, `theme_color #F3EEE3`,
`background_color`, icons 192/512).

### Part 6: docs, DevOps
- `README.md`: setup for **Windows PowerShell** and **macOS/Linux**, run tests, `createsuperuser`, demo logins
  (suborno, tanvir, sadia, famin, rafa / `demo12345`), warning never to seed a live server, what to configure
  before going live (`SECRET_KEY`, `ALLOWED_HOSTS`, PostgreSQL, SMS gateway, SMTP email, Redis, `collectstatic`),
  where to edit content (copy in `templates/`, areas list in `core/areas.py`, seed data in `seed_demo.py`).
- Multi-stage `Dockerfile` (slim base, non-root user, no dev deps, `PYTHONUNBUFFERED=1`, healthcheck on
  `/healthz/`), `.dockerignore`, `gunicorn.conf.py` (workers, timeout, access log to stdout).
- Deployment guide for **Render**: env vars, `migrate`, `collectstatic`, HTTPS and custom domain, rollback plan.
- `.github/workflows/ci.yml`: install, `ruff check`, `manage.py check --deploy` (with prod env set),
  `makemigrations --check`, `manage.py test`. `.pre-commit-config.yaml` (Ruff, whitespace, secrets scan).
- Pre-launch checklist (`check --deploy` clean, `DEBUG=False`, secrets rotated, backups tested, 404/500 verified,
  SSL grade, security headers, Lighthouse mobile 90+ with LCP < 2.5s, CLS < 0.1, INP < 200ms, real-device tests
  on iPhone Safari and Android Chrome, uptime monitoring, analytics consent).
- Optional Sentry hook, off by default: `SENTRY_DSN` is in `.env.example` but **not wired**; add guarded init in
  `production.py` plus `sentry-sdk` only if desired.

## 7. First things to do after unzipping (nothing was ever executed)
1. `python -m venv .venv`, activate, `pip install -r requirements-dev.txt` (versions were pinned offline;
   run `pip-audit` and fix any that do not resolve).
2. **`python manage.py makemigrations core`** and commit the result (no migrations were generated).
3. `python manage.py check`, then `python manage.py test`; fix first-run errors. Likely hot spots:
   `core/services.py` (circle-priority `Exists` subquery in `search_rides`; verify with
   `test_circle_rides_come_first`), template rendering in view tests, `{% static %}` references to files that
   do not exist yet.
4. `ruff check --fix .` (import ordering in `services.py`, a few unused names in tests, `assertTrue(mock)` and
   `assertTrue(ValidationError)` filler lines in tests can simply be deleted).
5. `python manage.py seed_demo` and click through: sign up, verify (code prints in the console), post, request,
   accept, complete, review.

## 8. Known gaps and risks
- Login lockout uses `REMOTE_ADDR` only (not forgeable); behind a proxy that means the proxy IP unless the
  platform passes it through properly. Per-process cache means a looser limit with several workers unless
  `REDIS_URL` is set.
- No rate limit on password-reset or resend-email endpoints yet (the OTP resend has a 60s throttle).
- `CompressedManifestStaticFilesStorage` fails on any missing static reference.
- CSP: strict nonce policy outside the admin and outside DEBUG. With a Google Maps key the policy adds
  `style-src-attr 'unsafe-inline'` because Maps injects inline styles. Plausible loads without SRI (documented).
- The `fonts.css` fallback metric overrides are starting values, not measured.
- Terms and Privacy are drafts and need legal review. The footer states the platform takes no cut: confirm that
  is true before launch.
- Bangla names: fonts fall back to Noto Sans/Serif Bengali stacks; test real Bangla strings.

## 9. Prompt to give the other AI
> You are finishing a Django 5.2 project, RideMate (zip attached, plus this brief). Do Part 5 then Part 6
> exactly as listed in section 6, honouring section 4 (names), section 5 (CSS contract) and the `data-*` hook
> table. Do not rename URL names, templates, classes or hooks. Output every file in full with its exact path,
> no ellipses. Keep initial JS under 150KB gzipped, all JS optional, copy human and specific (no filler words
> like "seamless", "elevate", "journey"), no invented facts, clients, metrics or links. When done, list every
> file added or changed and the commands to run the tests and the app.
