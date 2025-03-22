import json
import os
from datetime import timedelta

import pygal
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.utils import timezone
from impossible_travel.models import Alert, User
from pygal.style import Style


def _load_data(name):
    DATA_PATH = os.path.join(settings.CERTEGO_DJANGO_PROJ_BASE_DIR, "impossible_travel/dashboard/")  # pylint: disable=invalid-name
    with open(os.path.join(DATA_PATH, name + ".json"), encoding="utf-8") as file:
        data = json.load(file)
    return data


def users_pie_chart(start, end):
    custom_style = Style(
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
        legend_font_size=25,
        tooltip_font_size=25,
    )
    pie_chart = pygal.Pie(style=custom_style, width=1000, height=650)

    pie_chart.add("No risk", User.objects.filter(updated__range=(start, end), risk_score="No risk").count())
    pie_chart.add("Low", User.objects.filter(updated__range=(start, end), risk_score="Low").count())
    pie_chart.add("Medium", User.objects.filter(updated__range=(start, end), risk_score="Medium").count())
    pie_chart.add("High", User.objects.filter(updated__range=(start, end), risk_score="High").count())
    return pie_chart.render(disable_xml_declaration=True)


def alerts_line_chart(start, end):
    custom_style = Style(
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
                    login_raw_data__timestamp__range=(date_range[i].strftime("%Y-%m-%dT%H:%M:%S.%fZ"), date_range[i + 1].strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
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
                    login_raw_data__timestamp__range=(date_range[i].strftime("%Y-%m-%dT%H:%M:%S.%fZ"), date_range[i + 1].strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
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
                    login_raw_data__timestamp__range=(date_range[i].strftime("%Y-%m-%dT%H:%M:%S.%fZ"), date_range[i + 1].strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
                ).count()
            )
    line_chart.x_labels = map(str, date_str)
    line_chart.add("", alerts_in_range)
    return line_chart.render(disable_xml_declaration=True)


def world_map_chart(start, end):
    custom_style = Style(
        background="transparent",
        plot_background="transparent",
        foreground="#dee2e6",
        foreground_strong="#dee2e6",
        foreground_subtle="#dee2e6",
        opacity=".7",
        opacity_hover=".9",
        transition="400ms ease-in",
        colors=("#3174b0", "#00acac", "#408fa8"),
        value_font_size=1,
        tooltip_font_size=2.5,
        major_label_font_size=1,
        label_font_size=1,
        value_label_font_size=4,
    )
    map_chart = pygal.maps.world.World(  # pylint: disable=no-member
        style=custom_style,
        width=380,
        height=130,
        show_legend=False,
    )
    countries = _load_data("countries")
    tmp = {}
    for key, value in countries.items():
        country_alerts = Alert.objects.filter(
            login_raw_data__timestamp__range=(start.strftime("%Y-%m-%dT%H:%M:%S.%fZ"), end.strftime("%Y-%m-%dT%H:%M:%S.%fZ")), login_raw_data__country=value
        ).count()
        if country_alerts == 0:
            tmp[key] = None
        else:
            tmp[key] = country_alerts
    map_chart.add("Alerts", tmp)
    return map_chart.render_data_uri()
