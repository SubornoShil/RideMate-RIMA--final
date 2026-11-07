from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from accounts.forms import LinkedErrorsMixin
from accounts.models import UserProfile

from .models import RidePost

COORDINATE_BOUNDS = {"lat": (20.0, 27.0), "lng": (88.0, 93.0)}


class SearchForm(LinkedErrorsMixin, forms.Form):
    start = forms.CharField(required=False, max_length=120, label="From")
    end = forms.CharField(required=False, max_length=120, label="To")
    vehicle = forms.ChoiceField(
        required=False, choices=[("", "Any vehicle"), *RidePost.Vehicle.choices]
    )
    women_only = forms.BooleanField(required=False, label="Women-only rides")


class RideForm(LinkedErrorsMixin, forms.ModelForm):
    available_seats = forms.IntegerField(min_value=1, max_value=6, label="Seats")
    fare_per_seat = forms.IntegerField(
        min_value=0, initial=0, label="Fare per person (taka)",
        help_text="Use 0 when the fare is simply shared.",
    )

    class Meta:
        model = RidePost
        fields = [
            "start_location", "end_location", "departure_time", "vehicle_type",
            "available_seats", "fare_per_seat", "note", "female_only",
            "start_latitude", "start_longitude", "end_latitude", "end_longitude",
        ]
        labels = {"start_location": "Pick-up", "end_location": "Destination"}
        widgets = {
            "start_location": forms.TextInput(attrs={"list": "dhaka-areas", "autocomplete": "off"}),
            "end_location": forms.TextInput(attrs={"list": "dhaka-areas", "autocomplete": "off"}),
            "departure_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "note": forms.Textarea(attrs={"rows": 3}),
            "start_latitude": forms.HiddenInput(),
            "start_longitude": forms.HiddenInput(),
            "end_latitude": forms.HiddenInput(),
            "end_longitude": forms.HiddenInput(),
        }

    def __init__(self, *args, profile: UserProfile, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile = profile
        self.fields["departure_time"].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"]
        if profile.gender != UserProfile.Gender.FEMALE:
            del self.fields["female_only"]
        else:
            self.fields["female_only"].label = "Women-only ride"

    def clean_departure_time(self):
        departure = self.cleaned_data["departure_time"]
        if departure <= timezone.now():
            raise ValidationError("Pick a departure time in the future.")
        return departure

    def _clean_coordinate(self, name: str, axis: str):
        value = self.cleaned_data.get(name)
        low, high = COORDINATE_BOUNDS[axis]
        # Coordinates come from a hidden field; drop anything outside Bangladesh.
        return value if value is not None and low <= value <= high else None

    def clean_start_latitude(self):
        return self._clean_coordinate("start_latitude", "lat")

    def clean_end_latitude(self):
        return self._clean_coordinate("end_latitude", "lat")

    def clean_start_longitude(self):
        return self._clean_coordinate("start_longitude", "lng")

    def clean_end_longitude(self):
        return self._clean_coordinate("end_longitude", "lng")

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("start_location"), cleaned.get("end_location")
        if start and end and start.strip().lower() == end.strip().lower():
            self.add_error("end_location", "Pick-up and destination must be different.")
        if cleaned.get("female_only") and self.profile.gender != UserProfile.Gender.FEMALE:
            self.add_error(None, "Only women can post women-only rides.")
        return cleaned
