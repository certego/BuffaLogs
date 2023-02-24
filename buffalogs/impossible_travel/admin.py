from django.contrib import admin

from .models import Alert, Login, TaskSettings, User


@admin.register(Login)
class LoginAdmin(admin.ModelAdmin):
    list_display = ("id", "get_username", "timestamp", "latitude", "longitude", "country", "user_agent")
    search_fields = ("id", "user__username", "user_agent")

    @admin.display(description="username")
    def get_username(self, obj):
        return obj.user.username


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "created", "updated", "risk_score")
    search_fields = ("id", "username", "risk_score")


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("id", "get_username", "created", "name", "description", "login_raw_data")
    search_fields = ("user__username", "name")

    @admin.display(description="username")
    def get_username(self, obj):
        return obj.user.username


@admin.register(TaskSettings)
class TaskSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "created", "updated", "task_name", "start_date", "end_date")
    search_fields = ("id", "task_name", "start_date")
