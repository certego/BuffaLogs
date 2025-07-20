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
from django.urls import path, include
from impossible_travel.views import alerts, charts, ingestion, logins, users

urlpatterns = [
    # Users
    path("api/users/", users.list_users, name="list_users"),  # GET
    path("api/users/<int:id>/", users.detail_user, name="detail_user"),  # GET

    # Logins
    path("api/users/<int:id>/logins/unique/", logins.unique_logins, name="unique_logins"),
    path("api/users/<int:id>/logins/all/", logins.all_logins, name="all_logins"),

    # Alerts
    # User-specific alerts
    path("api/users/<int:id>/alerts/", alerts.user_alerts, name="user_alerts"),

# User risk score
    path("api/users/<int:id>/risk-score/", users.risk_score_api, name="risk_score"),

# General alert APIs
    path("api/alerts/", alerts.list_alerts, name="alerts_list"),  # renamed from alerts_api
    path("api/alerts/recent/", alerts.recent_alerts, name="alerts_recent"),  # renamed from get_last_alerts
    path("api/alerts/export/", alerts.export_alerts_csv, name="alerts_export"), 
    path("api/alerts/types/", alerts.alert_types, name="alert_types"), 

    # Analytics
   # charts / analytics endpoints
    path("api/analytics/users/pie/", charts.users_pie_chart, name="users_pie_chart"),
    path("api/analytics/alerts/line/", charts.alerts_line_chart, name="alerts_line_chart"),
    path("api/analytics/world-map/", charts.world_map, name="world_map"),
    path("api/users/<int:id>/analytics/login-timeline/", charts.user_login_timeline, name="user_login_timeline"),

    path("api/users/<int:id>/analytics/device-usage/", users.user_device_usage_api, name="device_usage"),
    path("api/users/<int:id>/analytics/login-frequency/", users.user_login_frequency_api, name="login_frequency"),
    path("api/users/<int:id>/analytics/time-of-day/", users.user_time_of_day_api, name="time_of_day"),
    path("api/users/<int:id>/analytics/geo-distribution/", users.user_geo_distribution_api, name="geo_distribution"),

    # Ingestion
    path("api/ingestion/sources/", ingestion.get_ingestion_sources, name="ingestion_sources"),
    path("api/ingestion/sources/active/", ingestion.get_active_ingestion_source, name="active_ingestion_source"),
    path("api/ingestion/sources/<str:source>/", ingestion.ingestion_source_config, name="source_config"),

    
    path("authentication/", include("authentication.urls")),

]
# Note: The order of urlpatterns matters. More specific patterns should come before more general ones.
