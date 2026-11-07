from django.contrib import admin, messages

from trust.services import log_moderation

from . import services
from .models import RidePost, RideRequest


@admin.register(RidePost)
class RidePostAdmin(admin.ModelAdmin):
    list_display = ("start_location", "end_location", "departure_time", "vehicle_type",
                    "female_only", "available_seats", "fare_per_seat", "status", "creator")
    list_filter = ("status", "vehicle_type", "female_only")
    search_fields = ("start_location", "end_location", "creator__user__username")
    list_select_related = ("creator__user",)
    date_hierarchy = "departure_time"
    actions = ["cancel_rides"]

    @admin.action(description="Cancel selected rides")
    def cancel_rides(self, request, queryset):
        count = 0
        for ride_id in queryset.values_list("pk", flat=True):
            if services.moderator_cancel_ride(ride_id):
                log_moderation(request.user, f"ride:{ride_id}", "cancel ride")
                count += 1
        self.message_user(request, f"Cancelled {count} ride(s).", messages.SUCCESS)


@admin.register(RideRequest)
class RideRequestAdmin(admin.ModelAdmin):
    list_display = ("ride", "requester", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("requester__user__username", "ride__start_location", "ride__end_location")
    list_select_related = ("ride", "requester__user")
