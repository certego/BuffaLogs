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
from django.urls import path
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
    path("users/<int:pk_user>/alerts/get_alerts", views.get_alerts, name="get_alerts"),
    path("users/<int:pk_user>/alerts", views.alerts, name="alerts"),
]
