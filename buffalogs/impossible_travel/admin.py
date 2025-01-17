from django.contrib import admin
from django.utils import timezone

from .forms import AlertAdminForm, ConfigAdminForm, UserAdminForm
from .models import Alert, Config, Login, TaskSettings, User, UsersIP


@admin.register(Login)
class LoginAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created",
        "updated",
        "get_username",
        "timestamp_display",
        "latitude",
        "longitude",
        "country",
        "user_agent",
        "index",
        "ip",
        "event_id",
    )
    search_fields = ("id", "user__username", "user_agent", "index", "event_id", "ip")

    @admin.display(description="username")
    def get_username(self, obj):
        return obj.user.username

    def timestamp_display(self, obj):
        # Usa strftime per personalizzare il formato
        return obj.timestamp.astimezone(timezone.get_current_timezone()).strftime("%b %d, %Y, %I:%M:%S %p %Z")


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    form = UserAdminForm
    list_display = ("id", "username", "created", "updated", "get_risk_score_value")
    search_fields = ("id", "username", "risk_score")

    @admin.display(description="risk_score")
    def get_risk_score_value(self, obj):
        return obj.risk_score


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    form = AlertAdminForm
    list_display = ("id", "created", "updated", "get_username", "get_alert_value", "description", "login_raw_data", "is_vip")
    search_fields = ("user__username", "name", "is_vip")

    @admin.display(description="username")
    def get_username(self, obj):
        return obj.user.username

    @admin.display(description="name")
    def get_alert_value(self, obj):
        return obj.name


@admin.register(TaskSettings)
class TaskSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "created", "updated", "task_name", "start_date", "end_date")
    search_fields = ("id", "task_name", "start_date")


@admin.register(Config)
class ConfigsAdmin(admin.ModelAdmin):
    form = ConfigAdminForm
    fieldsets = [
        ("Detection filters - users", {"fields": ("ignored_users", "enabled_users", "vip_users", "alert_is_vip_only", "alert_minimum_risk_score")}),
        ("Detection filters - location", {"fields": ("ignored_ips", "allowed_countries")}),
        ("Detection filters - devices", {"fields": ("ignored_ISPs", "ignore_mobile_logins")}),
        ("Detection filters - alerts", {"fields": ("filtered_alerts_types",)}),
        ("Detection setup - Impossible Travel alerts", {"fields": ("distance_accepted", "vel_accepted")}),
        ("Detection setup - Clean models", {"fields": ("user_max_days", "login_max_days", "alert_max_days", "ip_max_days")}),
    ]
    list_display = ("created", "updated", "ignored_users", "ignored_ips", "ignored_ISPs", "allowed_countries", "vip_users")
    search_fields = ("allowed_countries", "vip_users")


@admin.register(UsersIP)
class UsersIPAdmin(admin.ModelAdmin):
    list_display = ("id", "created", "updated", "get_username", "ip")
    search_fields = ("id", "user__username", "ip")

    @admin.display(description="username")
    def get_username(self, obj):
        return obj.user.username
