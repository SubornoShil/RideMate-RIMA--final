from django import forms

from accounts.forms import LinkedErrorsMixin
from accounts.phone import normalize_bd_phone


class ReviewForm(LinkedErrorsMixin, forms.Form):
    score = forms.TypedChoiceField(
        choices=[(n, f"{n} star{'s' if n > 1 else ''}") for n in range(5, 0, -1)],
        coerce=int, widget=forms.RadioSelect,
    )
    comment = forms.CharField(
        required=False, max_length=400, widget=forms.Textarea(attrs={"rows": 3})
    )


class GuardianForm(LinkedErrorsMixin, forms.Form):
    guardian_name = forms.CharField(max_length=80, label="Guardian's name")
    guardian_phone = forms.CharField(
        label="Guardian's mobile number",
        widget=forms.TextInput(attrs={"type": "tel", "inputmode": "tel"}),
    )

    def clean_guardian_phone(self):
        return normalize_bd_phone(self.cleaned_data["guardian_phone"])


class CircleJoinForm(LinkedErrorsMixin, forms.Form):
    code = forms.CharField(max_length=20, label="Circle code")
