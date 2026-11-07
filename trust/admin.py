from django.contrib import admin

from .models import Circle, GuardianContact, ModerationLog, Notification, Review


@admin.register(GuardianContact)
class GuardianContactAdmin(admin.ModelAdmin):
    list_display = ("guardian_name", "guardian_phone", "user")
    search_fields = ("guardian_name", "guardian_phone", "user__user__username")
    list_filter = ("user__gender",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("ride", "rater", "rated_user", "score", "rater_weight", "created_at")
    list_filter = ("score", "rater_weight")
    search_fields = ("rater__user__username", "rated_user__user__username", "comment")
    list_select_related = ("ride", "rater__user", "rated_user__user")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "kind", "message", "is_read", "created_at")
    list_filter = ("kind", "is_read")
    search_fields = ("message", "user__user__username")


@admin.register(ModerationLog)
class ModerationLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "moderator", "action", "target")
    list_filter = ("action",)
    search_fields = ("target", "action", "moderator__username")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Circle)
class CircleAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "member_total")
    search_fields = ("name", "code")
    list_filter = ("name",)
    filter_horizontal = ("members",)

    @admin.display(description="Members")
    def member_total(self, obj):
        return obj.members.count()
