from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "is_staff",
        "is_verified",
        "created_at",
        "updated_at",
        "avatar",
    )
    search_fields = ("id", "username", "email", "avatar")
