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
from impossible_travel import views

urlpatterns = [
    path("", views.homepage, name="homepage"),
    path("admin/", admin.site.urls),
    path("homepage/", views.homepage, name="homepage"),
    path("users/", views.users, name="users"),
    path("get_users/", views.get_users, name="get_users"),
    path("get_last_alerts/", views.get_last_alerts, name="get_last_alerts"),
    path("users/<int:pk_user>/unique_logins/get_unique_logins", views.get_unique_logins, name="get_unique_logins"),
    path("users/<int:pk_user>/unique_logins", views.unique_logins, name="unique_logins"),
    path("users/<int:pk_user>/all_logins/get_all_logins", views.get_all_logins, name="get_all_logins"),
    path("users/<int:pk_user>/all_logins", views.all_logins, name="all_logins"),
    path("users/alerts/get_alerts", views.get_alerts, name="get_alerts"),
    path("users/alerts", views.alerts, name="alerts"),
    path("users_pie_chart_api/", views.users_pie_chart_api, name="users_pie_chart_api"),
    path("alerts_line_chart_api/", views.alerts_line_chart_api, name="alerts_line_chart_api"),
    path("world_map_chart_api/", views.world_map_chart_api, name="world_map_chart_api"),
    path("api/export_alerts_csv/", views.export_alerts_csv, name="export_alerts_csv"),
    path("alerts_api/", views.alerts_api, name="alerts_api"),
    path("risk_score_api/", views.risk_score_api, name="risk_score_api"),
    path("authentication/", include("authentication.urls")),
    path("users/<int:pk>/login-timeline/", views.user_login_timeline_api, name="login_timeline_api"),
    path("users/<int:pk>/device-usage/", views.user_device_usage_api, name="device_usage_api"),
    path("users/<int:pk>/login-frequency/", views.user_login_frequency_api, name="login_frequency_api"),
    path("users/<int:pk>/time-of-day/", views.user_time_of_day_api, name="time_of_day_api"),
    path("users/<int:pk>/geo-distribution/", views.user_geo_distribution_api, name="geo_distribution_api"),
]
