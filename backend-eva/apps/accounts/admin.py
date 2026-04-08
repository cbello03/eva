"""Accounts admin registration."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import RefreshToken, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "display_name", "role", "is_active", "date_joined")
    list_filter = ("role", "is_active")
    search_fields = ("email", "display_name")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("display_name", "role", "timezone")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "display_name", "password1", "password2", "role"),
            },
        ),
    )


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "family_id", "is_revoked", "expires_at", "created_at")
    list_filter = ("is_revoked",)
    search_fields = ("user__email", "family_id")
    readonly_fields = ("token_hash", "family_id", "created_at", "updated_at")
