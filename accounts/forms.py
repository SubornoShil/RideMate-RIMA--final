from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db import transaction

from trust.models import Circle

from .models import UserProfile
from .phone import normalize_bd_phone


class LinkedErrorsMixin:
    """Point each invalid input at its error list (and help text) via aria-describedby."""

    def full_clean(self):
        super().full_clean()
        for name in self.errors:
            field = self.fields.get(name)
            if field is None:
                continue
            auto_id = self[name].auto_id
            ids = [f"{auto_id}_helptext"] if field.help_text else []
            field.widget.attrs["aria-describedby"] = " ".join([*ids, f"{auto_id}_errors"])


class SignUpForm(LinkedErrorsMixin, forms.Form):
    full_name = forms.CharField(max_length=150, label="Full name", widget=forms.TextInput(
        attrs={"autocomplete": "name"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    username = forms.CharField(
        max_length=150, validators=[UnicodeUsernameValidator()],
        widget=forms.TextInput(attrs={"autocomplete": "username", "autocapitalize": "none"}),
    )
    phone = forms.CharField(
        label="Mobile number",
        widget=forms.TextInput(attrs={"type": "tel", "inputmode": "tel", "autocomplete": "tel"}),
        help_text="01XXXXXXXXX, +8801XXXXXXXXX or 8801XXXXXXXXX.",
    )
    gender = forms.ChoiceField(choices=UserProfile.Gender.choices)
    password1 = forms.CharField(
        label="Password", strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Confirm password", strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    circle_code = forms.CharField(required=False, max_length=20, label="Circle code (optional)")
    accept_terms = forms.BooleanField(
        error_messages={"required": "You need to accept the Terms and Privacy to join."},
        label="I accept the Terms and Privacy",
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if get_user_model().objects.filter(username__iexact=username).exists():
            raise ValidationError("That username is taken.")
        return username

    def clean_phone(self):
        phone = normalize_bd_phone(self.cleaned_data["phone"])
        if UserProfile.objects.filter(phone_number=phone).exists():
            raise ValidationError("An account with this number already exists.")
        return phone

    def clean_circle_code(self):
        code = self.cleaned_data.get("circle_code", "").strip().upper()
        if code and not Circle.objects.filter(code=code).exists():
            raise ValidationError("No circle uses that code.")
        return code

    def clean(self):
        cleaned = super().clean()
        first, second = cleaned.get("password1"), cleaned.get("password2")
        if first and second and first != second:
            self.add_error("password2", "The two passwords do not match.")
        elif first:
            candidate = User(username=cleaned.get("username", ""), email=cleaned.get("email", ""))
            try:
                validate_password(first, user=candidate)
            except ValidationError as exc:
                self.add_error("password1", exc)
        return cleaned

    @transaction.atomic
    def save(self) -> User:
        data = self.cleaned_data
        first_name, _, last_name = data["full_name"].strip().partition(" ")
        user = User.objects.create_user(
            username=data["username"], email=data["email"], password=data["password1"],
            first_name=first_name[:150], last_name=last_name.strip()[:150],
        )
        profile = UserProfile.objects.create(
            user=user, phone_number=data["phone"], gender=data["gender"]
        )
        if data["circle_code"]:
            Circle.objects.get(code=data["circle_code"]).members.add(profile)
        return user


class IdentifierForm(LinkedErrorsMixin, forms.Form):
    identifier = forms.CharField(
        max_length=254, label="Email or username",
        widget=forms.TextInput(attrs={"autocomplete": "username", "autocapitalize": "none"}),
    )


class PasswordStepForm(LinkedErrorsMixin, forms.Form):
    password = forms.CharField(
        strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "current-password"})
    )


class OtpForm(LinkedErrorsMixin, forms.Form):
    code = forms.CharField(
        min_length=6, max_length=6, label="6-digit code",
        widget=forms.TextInput(attrs={
            "inputmode": "numeric", "autocomplete": "one-time-code", "pattern": "[0-9]{6}",
        }),
    )

    def clean_code(self):
        code = self.cleaned_data["code"].strip()
        if not code.isdigit():
            raise ValidationError("The code is six digits.")
        return code
