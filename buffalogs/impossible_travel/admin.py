from django.contrib import admin

from .models import Alert, Config, Login, TaskSettings, User


@admin.register(Login)
class LoginAdmin(admin.ModelAdmin):
    list_display = ("id", "created", "updated", "get_username", "timestamp", "latitude", "longitude", "country", "user_agent", "index", "ip", "event_id")
    search_fields = ("id", "user__username", "user_agent", "index", "event_id", "ip")

    @admin.display(description="username")
    def get_username(self, obj):
        return obj.user.username


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "created", "updated", "risk_score")
    search_fields = ("id", "username", "risk_score")


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("id", "created", "updated", "get_username", "name", "description", "login_raw_data", "is_vip")
    search_fields = ("user__username", "name", "is_vip")

    @admin.display(description="username")
    def get_username(self, obj):
        return obj.user.username


@admin.register(TaskSettings)
class TaskSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "created", "updated", "task_name", "start_date", "end_date")
    search_fields = ("id", "task_name", "start_date")


@admin.register(Config)
class ConfigsAdmin(admin.ModelAdmin):
    list_display = ("created", "updated", "allowed_countries", "vip_users")
    search_fields = ("allowed_countries", "vip_users")
