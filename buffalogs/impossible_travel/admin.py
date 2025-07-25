from django.contrib import admin
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from impossible_travel.forms import (
    AlertAdminForm,
    ConfigAdminForm,
    TaskSettingsAdminForm,
    UserAdminForm,
)
from impossible_travel.models import (
    Alert,
    Config,
    Login,
    TaskSettings,
    User,
    UsersIP,
)


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
        "ip",
        "user_agent",
        "event_id",
        "index",
    )
    search_fields = (
        "id",
        "user__username",
        "user_agent",
        "index",
        "event_id",
        "ip",
        "country",
    )

    @admin.display(description="username")
    def get_username(self, obj):
        return obj.user.username

    @admin.display(description="timestamp")
    def timestamp_display(self, obj):
        # Usa strftime per personalizzare il formato
        return obj.timestamp.astimezone(
            timezone.get_current_timezone()
        ).strftime("%b %d, %Y, %I:%M:%S %p %Z")


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    form = UserAdminForm
    list_display = (
        "id",
        "username",
        "created",
        "updated",
        "get_risk_score_value",
    )
    search_fields = ("id", "username", "risk_score")

    @admin.display(description="risk_score")
    def get_risk_score_value(self, obj):
        return obj.risk_score


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    form = AlertAdminForm
    list_display = (
        "id",
        "created",
        "updated",
        "get_username",
        "get_alert_value",
        "description",
        "login_raw_data",
        "is_filtered_field_display",
        "filter_type",
        "is_vip",
    )
    search_fields = ("id", "user__username", "name")
    readonly_fields = (
        "name",
        "get_username",
        "login_raw_data",
        "description",
        "filter_type",
        "is_filtered_field_display",
        "is_vip",
        "notified_status",
    )

    @admin.display(description="username")
    def get_username(self, obj):
        return obj.user.username

    @admin.display(description="name")
    def get_alert_value(self, obj):
        return obj.name


@admin.register(TaskSettings)
class TaskSettingsAdmin(admin.ModelAdmin):
    form = TaskSettingsAdminForm
    list_display = (
        "id",
        "created",
        "updated",
        "task_name",
        "start_date",
        "end_date",
    )
    search_fields = ("id", "task_name", "start_date")


@admin.register(Config)
class ConfigsAdmin(admin.ModelAdmin):
    form = ConfigAdminForm
    fieldsets = [
        (
            "Detection filters - users",
            {
                "fields": (
                    "ignored_users",
                    "enabled_users",
                    "vip_users",
                    "alert_is_vip_only",
                    "alert_minimum_risk_score",
                    "risk_score_increment_alerts",
                )
            },
        ),
        (
            "Detection filters - location",
            {"fields": ("ignored_ips", "allowed_countries")},
        ),
        (
            "Detection filters - devices",
            {"fields": ("ignored_ISPs", "ignore_mobile_logins")},
        ),
        ("Detection filters - alerts", {"fields": ("filtered_alerts_types",)}),
        (
            "Detection setup - Alerts",
            {
                "fields": (
                    "distance_accepted",
                    "vel_accepted",
                    "atypical_country_days",
                    "threshold_user_risk_alert",
                )
            },
        ),
        (
            "Detection setup - Clean models",
            {
                "fields": (
                    "user_max_days",
                    "login_max_days",
                    "alert_max_days",
                    "ip_max_days",
                )
            },
        ),
    ]
    list_display = (
        "id",
        "created",
        "updated",
        "ignored_users",
        "enabled_users",
        "ignored_ips",
        "get_minimum_risk_score_value",
        "allowed_countries",
        "filtered_alerts_types",
        "alert_is_vip_only",
        "ignore_mobile_logins",
    )
    search_fields = ("id",)

    @admin.display(description="Alert minimum risk score")
    def get_minimum_risk_score_value(self, obj):
        return obj.alert_minimum_risk_score

    @admin.display(description="Threshold user risk alert:")
    def get_threshold_user_risk_alert(self, obj):
        return obj.threshold_user_risk_alert

    def save_model(self, request, obj, form, change):
        if change:
            changes = []
            for field in form.changed_data:
                old_value = form.initial.get(field)
                new_value = form.cleaned_data.get(field)

                # Aggiungi un log dettagliato con valori precedenti e nuovi
                changes.append(
                    f"{field} changed from {old_value} to {new_value}"
                )

            if changes:
                self.log_change(request, obj, ", ".join(changes))

        super().save_model(request, obj, form, change)

    def log_change(self, request, obj, message):
        """Log the detailed message of changes"""
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(obj).pk,
            object_id=obj.pk,
            object_repr=str(obj),
            action_flag=CHANGE,
            change_message=message,
        )


@admin.register(UsersIP)
class UsersIPAdmin(admin.ModelAdmin):
    list_display = ("id", "created", "updated", "get_username", "ip")
    search_fields = ("id", "user__username", "ip")

    @admin.display(description="username")
    def get_username(self, obj):
        return obj.user.username
