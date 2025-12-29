from collections import defaultdict
from datetime import timedelta

import pygal
import pygal.style
from dateutil.relativedelta import relativedelta
from django.db.models import Count
from django.utils import timezone
from impossible_travel.models import Alert, Login, User
from impossible_travel.views.utils import read_config
from pygal_maps_world.maps import World

pie_custom_style = pygal.style.Style(
    background="transparent",
    plot_background="transparent",
    foreground="#dee2e6",
    foreground_strong="#dee2e6",
    foreground_subtle="#dee2e6",
    transition="400ms ease-in",
    opacity="0.7",
    opacity_hover="0.9",
    colors=("#3174b0", "#8753de", "#f59c1a", "#ff3333"),
    value_colors=("#fff"),
    legend_font_size=14,
    tooltip_font_size=14,
)
line_custom_style = pygal.style.Style(
    background="transparent",
    plot_background="transparent",
    foreground="#dee2e6",
    foreground_strong="#ffffff",
    foreground_subtle="#aaaaaa",
    opacity=".7",
    opacity_hover=".9",
    transition="400ms ease-in",
    colors=("#3174b0", "#408fa8"),
    tooltip_font_size=14,
    x_labels_font_size=12,
)

world_custom_style = pygal.style.Style(
    background="transparent",
    plot_background="transparent",
    foreground="#dee2e6",
    foreground_strong="#dee2e6",
    foreground_subtle="#dee2e6",
    opacity=".7",
    opacity_hover=".9",
    transition="400ms ease-in",
    colors=("#3174b0", "#00acac", "#408fa8"),
    value_font_size=10,
    tooltip_font_size=14,
    major_label_font_size=10,
    label_font_size=10,
    value_label_font_size=12,
)


def users_pie_chart(start, end):
    pie_chart = pygal.Pie(style=pie_custom_style, width=1000, height=650)

    pie_chart.add("No risk", User.objects.filter(updated__range=(start, end), risk_score="No risk").count())
    pie_chart.add("Low", User.objects.filter(updated__range=(start, end), risk_score="Low").count())
    pie_chart.add("Medium", User.objects.filter(updated__range=(start, end), risk_score="Medium").count())
    pie_chart.add("High", User.objects.filter(updated__range=(start, end), risk_score="High").count())
    return pie_chart.render(disable_xml_declaration=True)


def alerts_line_chart(start, end):
    custom_style = pygal.style.Style(
        background="transparent",
        plot_background="transparent",
        foreground="#dee2e6",
        foreground_strong="#dee2e6",
        foreground_subtle="#dee2e6",
        opacity=".7",
        opacity_hover=".9",
        transition="400ms ease-in",
        colors=("#3174b0", "#408fa8"),
        tooltip_font_size=20,
        x_labels_font_size=20,
    )
    line_chart = pygal.StackedBar(fill=True, show_legend=False, style=custom_style, width=1200, height=550, x_label_rotation=20)
    date_range = []
    alerts_in_range = []
    date_str = []
    delta_timestamp = end - start
    if delta_timestamp.days < 1:
        while start <= end:
            date_range.append(start)
            date_str.append(start.strftime("%H:%M:%S"))
            start = start + timedelta(minutes=59, seconds=59)
            date_range.append(start)
            start = start + timedelta(seconds=1)
        for i in range(0, len(date_range) - 2, 2):
            alerts_in_range.append(
                Alert.objects.filter(
                    login_raw_data__timestamp__range=(
                        date_range[i].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                        date_range[i + 1].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    )
                ).count()
            )
    elif delta_timestamp.days >= 1 and delta_timestamp.days <= 31:
        while start <= end:
            date_range.append(start)
            date_str.append(start.strftime("%Y-%m-%d"))
            start = start + timedelta(hours=23, minutes=59, seconds=59)
            date_range.append(start)
            start = start + timedelta(seconds=1)
        for i in range(0, len(date_range) - 2, 2):
            alerts_in_range.append(
                Alert.objects.filter(
                    login_raw_data__timestamp__range=(
                        date_range[i].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                        date_range[i + 1].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    )
                ).count()
            )
    else:
        start = timezone.datetime(start.year, start.month, 1)
        end = end.replace(tzinfo=None)
        while start <= end:
            date_range.append(start)
            date_str.append(start.strftime("%B %Y"))
            start = start + relativedelta(months=1)
            date_range.append(start)
        for i in range(0, len(date_range) - 2, 2):
            alerts_in_range.append(
                Alert.objects.filter(
                    login_raw_data__timestamp__range=(
                        date_range[i].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                        date_range[i + 1].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    )
                ).count()
            )
    line_chart.x_labels = map(str, date_str)
    line_chart.add("", alerts_in_range)
    return line_chart.render(disable_xml_declaration=True)


def world_map_chart(start, end):
    map_chart = pygal.maps.world.World(
        style=world_custom_style,
        width=380,
        height=130,
        show_legend=False,
    )
    countries = read_config("countries_list.json")
    tmp = {}
    for key, value in countries.items():
        country_alerts = Alert.objects.filter(
            login_raw_data__timestamp__range=(
                start.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                end.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            ),
            login_raw_data__country=value,
        ).count()
        if country_alerts == 0:
            tmp[key] = None
        else:
            tmp[key] = country_alerts
    map_chart.add("Alerts", tmp)
    return map_chart.render_data_uri()


# -> user personal login activity dashboard
def user_login_timeline_chart(user, start, end):
    logins = Login.objects.filter(user=user, timestamp__range=(start, end))
    chart = pygal.DateTimeLine(x_label_rotation=20, style=line_custom_style, title="Login Timeline", width=1000, height=650)
    chart.add("Logins", [(login.timestamp, 1) for login in logins])
    return chart.render(disable_xml_declaration=True)


def user_device_usage_chart(user, start, end):
    devices = Login.objects.filter(user=user, timestamp__range=(start, end)).values("user_agent").annotate(count=Count("id"))

    pie_chart = pygal.Pie(style=pie_custom_style, legend=True, show_labels=False, width=1000, height=650)
    pie_chart.title = "Device Usage"
    for d in devices:
        pie_chart.add(d["user_agent"], d["count"])
    return pie_chart.render(disable_xml_declaration=True)


def user_login_frequency_chart(user, start, end):
    total_days = (end - start).days + 1
    days = [start + timedelta(days=i) for i in range(total_days)]

    daily_counts = {day.date(): 0 for day in days}

    for login in Login.objects.filter(user=user, timestamp__range=(start, end)):
        login_day = login.timestamp.date()
        if login_day in daily_counts:
            daily_counts[login_day] += 1
        else:
            daily_counts[login_day] = 1

    line_chart = pygal.Line(style=line_custom_style, width=1000, height=650)
    line_chart.title = f"Login Frequency ({start.date()} to {end.date()})"
    line_chart.x_labels = [d.date().isoformat() for d in days]
    line_chart.x_title = "Date"
    line_chart.y_title = "Number of Logins"
    login_values = [daily_counts.get(d.date(), 0) for d in days]
    line_chart.add("Logins", login_values)

    return line_chart.render(disable_xml_declaration=True)


def user_time_of_day_chart(user, start, end):
    counts = defaultdict(lambda: defaultdict(int))
    qs = Login.objects.filter(user=user, timestamp__range=(start, end))
    for login in qs:
        h = login.timestamp.hour
        w = login.timestamp.weekday()
        counts[h][w] += 1

    chart = pygal.StackedBar(style=line_custom_style, width=1000, height=650)
    chart.title = "Hourly Logins by Weekday"
    chart.x_labels = [f"{h:02d}:00" for h in range(24)]

    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for idx, name in enumerate(weekdays):
        data = [counts[h].get(idx, 0) for h in range(24)]
        chart.add(name, data)
    return chart.render(disable_xml_declaration=True)


def user_geo_distribution_chart(user, start, end):
    logins = Login.objects.filter(user=user, timestamp__range=(start, end))
    country_data = logins.values("country").annotate(count=Count("id"))

    # Get alert counts per country for the user
    alerts = Alert.objects.filter(
        user=user,
        login_raw_data__timestamp__range=(
            start.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            end.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        ),
    )
    alert_by_country = {}
    for alert in alerts:
        country = alert.login_raw_data.get("country", "")
        if country:
            alert_by_country[country.lower()] = alert_by_country.get(country.lower(), 0) + 1

    countries = read_config("countries_list.json")
    name_to_code = {v.lower(): k for k, v in countries.items()}

    country_dict = {}
    for entry in country_data:
        country_name = entry["country"]
        code = name_to_code.get(country_name.lower())
        if code:
            login_count = entry["count"]
            alert_count = alert_by_country.get(country_name.lower(), 0)
            # Create tooltip with country name, logins, and alerts
            country_dict[code] = {
                "value": login_count,
                "label": f"{country_name}: {login_count} logins, {alert_count} alerts",
            }

    world_chart = World(style=world_custom_style, width=1000, height=650)
    world_chart.title = "Login Locations"
    world_chart.add("Logins", country_dict)

    return world_chart.render_data_uri()
