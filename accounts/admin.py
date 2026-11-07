from django.contrib import admin, messages

from trust.services import log_moderation

from .models import UserProfile

admin.site.site_header = "RideMate admin"
admin.site.site_title = "RideMate"
admin.site.index_title = "Moderation and content"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "phone_number", "gender", "trust_score", "is_verified",
                    "email_verified", "is_active_account", "created_at")
    list_filter = ("gender", "is_verified", "email_verified", "user__is_active")
    search_fields = ("user__username", "user__email", "user__first_name", "phone_number")
    readonly_fields = ("trust_score", "created_at")
    list_select_related = ("user",)
    actions = ["suspend_accounts", "reactivate_accounts"]

    @admin.display(boolean=True, description="Active")
    def is_active_account(self, obj):
        return obj.user.is_active

    @admin.action(description="Suspend selected accounts")
    def suspend_accounts(self, request, queryset):
        count = 0
        for profile in queryset.select_related("user").exclude(user=request.user):
            if profile.user.is_active:
                profile.user.is_active = False
                profile.user.save(update_fields=["is_active"])
                log_moderation(request.user, f"user:{profile.user.username}", "suspend account")
                count += 1
        self.message_user(request, f"Suspended {count} account(s).", messages.SUCCESS)

    @admin.action(description="Reactivate selected accounts")
    def reactivate_accounts(self, request, queryset):
        count = 0
        for profile in queryset.select_related("user"):
            if not profile.user.is_active:
                profile.user.is_active = True
                profile.user.save(update_fields=["is_active"])
                log_moderation(request.user, f"user:{profile.user.username}", "reactivate account")
                count += 1
        self.message_user(request, f"Reactivated {count} account(s).", messages.SUCCESS)
