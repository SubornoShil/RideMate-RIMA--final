import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import password_validators_help_texts
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from . import services
from .decorators import profile_required
from .forms import IdentifierForm, OtpForm, PasswordStepForm, SignUpForm
from .http import client_ip, safe_next
from .services import OtpResult

logger = logging.getLogger(__name__)
GENERIC_LOGIN_ERROR = "That email, username or password did not work."


def signup(request):
    if request.user.is_authenticated:
        return redirect("rides:dashboard")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend="accounts.backends.IdentifierBackend")
        profile = services.get_profile(user)
        services.issue_otp(request.session, profile)
        services.send_confirmation_email(request, user)
        messages.success(request, "Welcome. We sent a code to your phone.")
        return redirect("accounts:verify_phone")
    return render(request, "signup.html", {
        "form": form, "password_rules": password_validators_help_texts(),
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect("rides:dashboard")
    session = request.session
    if request.GET.get("reset"):
        session.pop("login_identifier", None)
    ip = client_ip(request)

    if request.method == "POST" and request.POST.get("step") == "password":
        identifier = session.get("login_identifier", "")
        form = PasswordStepForm(request.POST)
        if not identifier:
            return redirect("accounts:login")
        if services.is_login_locked(identifier, ip):
            messages.error(request, "Too many attempts. Try again in 15 minutes.")
            return render(request, "login.html", {"step": "password", "form": form,
                                                  "identifier": identifier})
        if form.is_valid():
            user = authenticate(request, username=identifier, password=form.cleaned_data["password"])
            if user is not None:
                services.clear_login_failures(identifier, ip)
                session.pop("login_identifier", None)
                login(request, user)
                services.get_profile(user)
                return redirect(safe_next(request, "rides:dashboard"))
            services.register_login_failure(identifier, ip)
            form.add_error(None, GENERIC_LOGIN_ERROR)
        return render(request, "login.html", {"step": "password", "form": form,
                                              "identifier": identifier,
                                              "next": request.POST.get("next", "")})

    if request.method == "POST":
        form = IdentifierForm(request.POST)
        if form.is_valid():
            # Always advance, whether or not the account exists.
            session["login_identifier"] = form.cleaned_data["identifier"].strip()
            return render(request, "login.html", {
                "step": "password", "form": PasswordStepForm(),
                "identifier": session["login_identifier"], "next": request.POST.get("next", ""),
            })
        return render(request, "login.html", {"step": "identifier", "form": form})

    return render(request, "login.html", {
        "step": "identifier", "form": IdentifierForm(), "next": request.GET.get("next", ""),
    })


@require_POST
def logout_view(request):
    logout(request)
    return redirect("rides:home")


@profile_required
def verify_phone(request):
    profile = request.profile
    if profile.is_verified:
        return redirect("rides:dashboard")
    form = OtpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        result = services.check_otp(request.session, profile, form.cleaned_data["code"])
        if result is OtpResult.OK:
            messages.success(request, "Phone verified. You can post rides and send requests.")
            return redirect("rides:dashboard")
        if result is OtpResult.WRONG:
            left = services.otp_attempts_left(request.session)
            form.add_error("code", f"That code is wrong. {left} attempts left.")
        elif result is OtpResult.LOCKED:
            form.add_error("code", "Too many wrong codes. Ask for a new one.")
        else:
            form.add_error("code", "That code expired or was never sent. Ask for a new one.")
    return render(request, "verify_phone.html", {
        "form": form,
        "resend_wait": services.otp_resend_wait(request.session),
        "code_sent": bool(request.session.get("otp_hash")),
    })


@require_POST
@profile_required
def resend_otp(request):
    if request.profile.is_verified:
        return redirect("rides:dashboard")
    wait = services.otp_resend_wait(request.session)
    if wait:
        messages.warning(request, f"Please wait {wait} seconds before asking again.")
    elif services.issue_otp(request.session, request.profile):
        messages.success(request, "A new code is on its way.")
    else:
        messages.error(request, "We could not send the code. Try again shortly.")
    return redirect("accounts:verify_phone")


def verify_email(request, token):
    profile = services.confirm_email_token(token)
    if profile is None:
        messages.error(request, "That confirmation link is invalid or has expired.")
    else:
        messages.success(request, "Email confirmed.")
    return redirect("rides:dashboard" if request.user.is_authenticated else "accounts:login")


@require_POST
@profile_required
def resend_email(request):
    if request.profile.email_verified:
        return redirect("rides:dashboard")
    if services.send_confirmation_email(request, request.user):
        messages.success(request, "Confirmation email sent.")
    else:
        messages.error(request, "We could not send the email. Try again shortly.")
    return redirect(safe_next(request, "rides:dashboard"))
