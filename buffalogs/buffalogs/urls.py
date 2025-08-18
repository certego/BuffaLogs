from django.contrib import admin
from django.urls import include, path
from impossible_travel.views import alerts, charts, ingestion, logins, users

urlpatterns = [
    path("", charts.homepage, name="homepage"),
    path("admin/", admin.site.urls),
    # Template response
    path("homepage/", charts.homepage, name="homepage"),
    path("users/", users.users_template_view, name="users"),
    path("users/<int:user_id>/unique_logins", users.unique_login_template_view, name="unique_logins"),
    path("users/<int:user_id>/all_logins", users.all_login_template_view, name="all_logins"),
    path("alerts/", alerts.alert_template_view, name="alerts"),
    # path("users/<int:user_id>/alerts", users.alert_template_view, name="user_alerts"),
    # API response
    path("api/users/", users.list_users, name="list_users"),
    path("api/users/<int:user_id>/", users.user_details, name="user_details"),
    # path("api/users/login/all/", logins.get_user_logins, name="get_user_logins"),
    # path("api/users/login/unique/", logins.get_user_unique_logins, name="get_user_unique_logins"),
    # path("users/<int:pk_user>/unique_logins/get_unique_logins", logins.get_unique_logins, name="get_unique_logins"),
    # path("users/<int:pk_user>/all_logins/get_all_logins", logins.get_all_logins, name="get_all_logins"),
    path("api/alerts/", alerts.list_alerts, name="get_alerts"),
    path("users_pie_chart_api/", charts.users_pie_chart_api, name="users_pie_chart_api"),
    path("users/<int:pk>/login-timeline/", charts.user_login_timeline_api, name="login_timeline_api"),
    path("users/<int:pk>/device-usage/", users.user_device_usage_api, name="device_usage_api"),
    path("users/<int:pk>/login-frequency/", users.user_login_frequency_api, name="login_frequency_api"),
    path("users/<int:pk>/time-of-day/", users.user_time_of_day_api, name="time_of_day_api"),
    path("users/<int:pk>/geo-distribution/", users.user_geo_distribution_api, name="geo_distribution_api"),
    path("get_last_alerts/", alerts.get_last_alerts, name="get_last_alerts"),
    path("risk_score_api/", users.risk_score_api, name="risk_score_api"),
    path("alerts_line_chart_api/", charts.alerts_line_chart_api, name="alerts_line_chart_api"),
    path("world_map_chart_api/", charts.world_map_chart_api, name="world_map_chart_api"),
    # path("alerts_api/", alerts.alerts_api, name="alerts_api"),
    path("authentication/", include("authentication.urls")),
    path("api/export_alerts_csv/", alerts.export_alerts_csv, name="export_alerts_csv"),
    path("api/alert_types/", alerts.alert_types, name="alert_types"),
    path("api/ingestion/sources/", ingestion.get_ingestion_sources, name="ingestion_sources_api"),
    path("api/ingestion/active_ingestion_source/", ingestion.get_active_ingestion_source, name="active_ingestion_source_api"),
    path("api/ingestion/<str:source>/", ingestion.ingestion_source_config, name="ingestion_source_config_api"),
    path("api/alerters/active-alerter/", alerts.get_active_alerter, name="active_alerter_api"),
    path("api/alerters/<str:alerter>/", alerts.alerter_config, name="alerter_config_api"),
    path("api/alerters/", alerts.get_alerters, name="get_alerters"),
    path("api/logins/", logins.login_api, name="list_logins"),
]
