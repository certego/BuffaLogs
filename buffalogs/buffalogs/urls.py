"""buffalogs URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from impossible_travel.views import alerts, charts, logins, users

urlpatterns = [
    path("", charts.homepage, name="homepage"),
    path("admin/", admin.site.urls),
    path("homepage/", charts.homepage, name="homepage"),
    path("users/", users.users, name="users"),
    path("get_users/", users.get_users, name="get_users"),
    path("get_last_alerts/", alerts.get_last_alerts, name="get_last_alerts"),
    path("users/<int:pk_user>/unique_logins/get_unique_logins", logins.get_unique_logins, name="get_unique_logins"),
    path("users/<int:pk_user>/unique_logins", users.unique_logins, name="unique_logins"),
    path("users/<int:pk_user>/all_logins/get_all_logins", logins.get_all_logins, name="get_all_logins"),
    path("users/<int:pk_user>/all_logins", users.all_logins, name="all_logins"),
    path("users/alerts/get_alerts", alerts.get_alerts, name="get_alerts"),
    path("users/alerts", users.alerts, name="alerts"),
    path("users_pie_chart_api/", charts.users_pie_chart_api, name="users_pie_chart_api"),
    path("alerts_line_chart_api/", charts.alerts_line_chart_api, name="alerts_line_chart_api"),
    path("world_map_chart_api/", charts.world_map_chart_api, name="world_map_chart_api"),
    path("api/export_alerts_csv/", alerts.export_alerts_csv, name="export_alerts_csv"),
    path("alerts_api/", alerts.alerts_api, name="alerts_api"),
    path("risk_score_api/", users.risk_score_api, name="risk_score_api"),
    path("authentication/", include("authentication.urls")),
    path("users/<int:pk>/login-timeline/", charts.user_login_timeline_api, name="login_timeline_api"),
    path("users/<int:pk>/device-usage/", users.user_device_usage_api, name="device_usage_api"),
    path("users/<int:pk>/login-frequency/", users.user_login_frequency_api, name="login_frequency_api"),
    path("users/<int:pk>/time-of-day/", users.user_time_of_day_api, name="time_of_day_api"),
    path("users/<int:pk>/geo-distribution/", users.user_geo_distribution_api, name="geo_distribution_api"),
]
