from django.contrib import admin
from django.urls import include, path
from impossible_travel.views import alerts, charts, ingestion, logins, users

urlpatterns = [
    path("admin/", admin.site.urls),
    path("authentication/", include("authentication.urls")),
    # Template response
    path("", charts.homepage, name="homepage"),
    path("homepage/", charts.homepage, name="homepage"),
    path("users/", users.users_template_view, name="users"),
    path("users/alerts", alerts.alert_template_view, name="alerts"),
    path("users/<int:user_id>/alerts", alerts.alert_template_view, name="alerts"),
    path("users/<int:user_id>/logins", users.all_login_template_view, name="all_logins"),
    path("users/<int:user_id>/unique_logins", users.unique_login_template_view, name="unique_logins"),
    # User APIs
    path("api/users/", users.list_users, name="list_users"),
    path("api/users/<int:user_id>/", users.user_details, name="user_details"),
    # Alert APIs
    path("api/alerts/", alerts.list_alerts, name="list_alerts"),
    path("api/alerts/types/", alerts.alert_types, name="alert_types"),
    path("api/alerts/recent/", alerts.recent_alerts, name="recent_alerts"),
    path("api/alerts/export/", alerts.export_alerts_csv, name="export_alerts_csv"),
    # Login APIs
    path("api/logins/", logins.login_api, name="logins"),
    path("api/users/<int:user_id>/logins", logins.get_user_logins, name="user_logins"),
    path("api/users/<int:user_id>/logins/unique/", logins.get_user_unique_logins, name="user_unique_logins"),
    # Analytics APIs
    path("api/analytics/chart/users/pie/", charts.users_pie_chart_api, name="users_pie_chart_api"),
    path("api/analytics/chart/world-map/", charts.world_map_chart_api, name="world_map_chart_api"),
    path("api/analytics/chart/alerts/line/", charts.alerts_line_chart_api, name="alerts_line_chart_api"),
    path("api/users/<int:pk>/analytics/login-timeline/", charts.user_login_timeline_api, name="login_timeline_api"),
    path("api/users/<int:pk>/analytics/device-usage/", users.user_device_usage_api, name="device_usage_api"),
    path("api/users/<int:pk>/analytics/login-frequency/", users.user_login_frequency_api, name="login_frequency_api"),
    path("api/users/<int:pk>/analytics/time-of-day/", users.user_time_of_day_api, name="time_of_day_api"),
    path("api/users/<int:pk>/analytics/geo-distribution/", users.user_geo_distribution_api, name="geo_distribution_api"),
    path("api/users/analytics/risk-score/", users.risk_score_api, name="risk_score_api"),
    # Ingestion APIs
    path("api/ingestion/sources/", ingestion.get_ingestion_sources, name="ingestion_sources_api"),
    path("api/ingestion/active_ingestion_source/", ingestion.get_active_ingestion_source, name="active_ingestion_source_api"),
    path("api/ingestion/<str:source>/", ingestion.ingestion_source_config, name="ingestion_source_config_api"),
    # Alerters APIs
    path("api/alerters/active-alerter/", alerts.get_active_alerter, name="active_alerter_api"),
    path("api/alerters/<str:alerter>/", alerts.alerter_config, name="alerter_config_api"),
    path("api/alerters/", alerts.get_alerters, name="get_alerters"),
]
