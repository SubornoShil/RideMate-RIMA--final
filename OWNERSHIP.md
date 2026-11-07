# RideMate: three apps, three owners

The project started as one Django app (`core`). It is now three apps with a clear job each, so three
people can each explain a complete part in a viva. One app = one member. Every member owns
**models, services (business rules), views, forms, urls, admin, templates and tests** of their app.

```
                accounts   (Member A: who you are)
                   ^
        rides      |      trust    (Member B: the trip)   (Member C: why you can trust it)
          ^________|________^
```

Dependency rule: `accounts` is the base layer. It only touches the other apps for the circle code on the
sign-up form and the moderation log in its admin. `trust` uses `accounts` and `rides`. `rides` uses `accounts` and the notification and
guardian helpers of `trust`. There are no circular imports.

## Member A: `accounts` (identity and platform security)

| Part | Files |
|---|---|
| Model | `UserProfile` (phone, gender, verified flags, trust score field) |
| Pages | sign up, two-step login, phone code (OTP), email confirmation |
| Rules | login lockout (5 tries, 15 min), 6-digit code with expiry and attempt limit, signed email token |
| Helpers | `phone.py` (Bangladeshi number check), `sms.py` (console / Twilio / HTTP), `backends.py` (login by email or username), `decorators.py` (`profile_required`, `verified_required`) |
| Platform | `config/` settings, `config/middleware.py` (CSP nonce, Permissions-Policy), Dockerfile, CI |
| Tests | `tests/test_signup_login.py`, `tests/test_otp.py`, `tests/test_misc.py` |

Viva questions Member A should be ready for: Why is login two steps and why does it always advance?
How is the OTP stored (hash in session, never the code)? Why a lockout keyed on identifier plus IP?
What does the CSP nonce protect against? Why Argon2? Why `REMOTE_ADDR` and not `X-Forwarded-For`?

## Member B: `rides` (the marketplace)

| Part | Files |
|---|---|
| Models | `RidePost`, `RideRequest` (constraints: max 6 seats, one request per rider per ride) |
| Pages | home and search, post a ride, ride detail, dashboard, accept / decline / cancel |
| Rules | women-only visibility, circle members first in search, request flow with row locks (`select_for_update`) so the last seat can never go to two people, complete and cancel |
| Helpers | `areas.py` (place suggestions), `utils.py` (participants), `seed_demo` command |
| Tests | `tests/test_rides.py` |

Viva questions: How is double-booking of the last seat prevented? Why is a women-only ride a 404 and
not a 403 for men? How does search rank circle rides? What do the model constraints enforce at the
database level?

## Member C: `trust` (trust and safety) and the front end

| Part | Files |
|---|---|
| Models | `Circle`, `GuardianContact`, `Review`, `Notification`, `ModerationLog` |
| Pages | ratings (star picker), profile with guardians and received ratings, notifications, circles, analytics (staff only) |
| Rules | weighted trust score (ratings from accounts younger than 7 days count half), rating only after the host completes the ride and only between people who shared it, guardian SMS when a seat is confirmed, moderation log |
| Front end | `static/css/main.css`, `static/js/*`, the hero map and road animation (`tools/build_maps.py`, `tools/build_roadscene.py`) |
| Tests | `tests/test_reviews_guardians.py` |

Viva questions: Show the trust-score formula with an example. Why are new accounts weighted 0.5?
What stops someone rating themselves or twice? What happens if a guardian SMS fails? Why generate the
map from latitude and longitude?

## Shared glue (explain it together)

`config/errors.py` (`RideError`), `config/urls.py` (includes the three apps), `templates/base.html`,
the error pages, `accounts/context_processors.py` and `trust/context_processors.py`.

## A fair note on size

Counting Python lines the apps are roughly accounts 770 (+ config 370), rides 850, trust 490. Member C
carries the front end on top, which is why trust looks smaller. If your group wants a different split,
the cleanest swap is moving `dashboard` between apps; everything else stays put.
